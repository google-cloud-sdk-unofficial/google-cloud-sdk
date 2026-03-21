# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Command to pause a pipeline."""

import datetime
import random
import subprocess
import time
from googlecloudsdk.api_lib.composer import dags_util
from googlecloudsdk.api_lib.composer import environments_util
from googlecloudsdk.api_lib.composer import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines.tools import composer_utils
from googlecloudsdk.command_lib.orchestration_pipelines.tools import gcs_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

DEFAULT_POLLING_TIME_SECONDS = datetime.timedelta(seconds=2)
POLL_JITTER_SECONDS = datetime.timedelta(seconds=0.5)
ORCHESTRATION_PIPELINES_DIRECTORY = "orchestration_pipelines"


@calliope_base.Hidden
@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class Pause(calliope_base.Command):
  """A command that pauses an orchestration pipeline."""

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._subprocess = subprocess

  @staticmethod
  def Args(parser):
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--environment",
        help=(
            "The target environment of the pipeline, as defined in"
            " deployment.yaml."
        ),
    )
    group.add_argument(
        "--runner",
        help="The full resource name to pause a pipeline from.",
    )
    parser.add_argument(
        "--bundle",
        required=True,
        help="The ID of the bundle the pipeline belongs to.",
    )
    parser.add_argument(
        "--pipeline",
        required=True,
        help="The ID of the pipeline to pause.",
    )
    parser.add_argument(
        "--async",
        action="store_true",
        dest="async_",
        help=(
            "If set, the command will return after updating the pipeline files"
            " and pause the pipeline asynchronously in the"
            " background."
        ),
    )

  def Run(self, args):
    api_version = util.GetApiVersion(self.ReleaseTrack())

    # 1. Retrieve the pipeline to be paused.
    list_filter = composer_utils.build_dags_filter_tags(
        bundle=args.bundle, pipeline=args.pipeline, is_current=True
    )
    resource_name = composer_utils.build_resource_name(
        args.environment, args.runner
    )
    environment_ref = resources.REGISTRY.ParseRelativeName(
        resource_name,
        collection="composer.projects.locations.environments",
        api_version=api_version,
    )
    list_dags_response = dags_util.ListDags(
        environment_ref,
        list_filter=list_filter,
    )

    if len(list_dags_response.dags) == 0:
      return {
          "result": "failed",
          "reason": "No pipeline found for given bundle and pipeline IDs.",
      }

    if len(list_dags_response.dags) > 1:
      return {
          "result": "failed",
          "reason": (
              "Multiple pipelines found for given bundle and pipeline IDs."
          ),
      }

    if composer_utils.get_pipeline_paused_status(list_dags_response.dags[0]):
      log.status.Print(f"Pipeline {args.pipeline} is already paused.")
      return {"result": "success"}

    # 2. Retrieve the environment storage bucket and build the manifest GCS
    # path.
    environment = environments_util.Get(environment_ref)
    if not environment.storageConfig or not environment.storageConfig.bucket:
      return {
          "result": "failed",
          "reason": (
              "Could not retrieve GCS storage bucket for Composer environment."
          ),
      }
    manifest_gcs_path = "gs://{}/{}/{}/{}".format(
        environment.storageConfig.bucket,
        ORCHESTRATION_PIPELINES_DIRECTORY,
        args.bundle,
        gcs_utils.MANIFEST_FILE_NAME,
    )

    try:
      # 3. Update the manifest file in GCS with retry logic and optimistic
      # locking.
      gcs_utils.UpdatePausedPipelinesInManifestWithRetry(
          self._subprocess, manifest_gcs_path, args.pipeline, "add"
      )
      log.status.Print(f"Successfully updated manifest for {args.bundle}.")

      # 4. Touch the pipeline's python file to trigger the Airflow scheduler to
      # pick up the changes in the next run.
      pipeline_gcs_path = "gs://{}/dags/{}/{}/{}.py".format(
          environment.storageConfig.bucket,
          ORCHESTRATION_PIPELINES_DIRECTORY,
          args.bundle,
          args.pipeline,
      )
      log.status.Print("Updating metadata for pipeline files...")
      gcs_utils.TouchPipelineFile(self._subprocess, pipeline_gcs_path)
    except (
        calliope_exceptions.BadFileException,
        calliope_exceptions.HttpException,
    ) as e:
      log.status.Print("Reverting manifest file...")
      gcs_utils.UpdatePausedPipelinesInManifestWithRetry(
          self._subprocess, manifest_gcs_path, args.pipeline, "remove"
      )
      return {
          "result": "failed",
          "reason": f"{str(e)}",
      }
    except ValueError as _:
      return {
          "result": "failed",
          "reason": "An unexpected error occurred while pausing the pipeline.",
      }

    if args.async_:
      log.status.Print(
          "Pipeline files were updated. Running in async mode, exiting..."
      )
      return {"result": "success"}

    # 5. Wait for the scheduler to pick up the changes and update the DAG.
    log.status.Print("Waiting for the pipeline to be paused...")
    while True:
      try:
        paused_dags_list = dags_util.ListDags(
            environment_ref, list_filter=list_filter
        )
        if paused_dags_list.dags and composer_utils.get_pipeline_paused_status(
            paused_dags_list.dags[0]
        ):
          return {"result": "success"}
        time.sleep(
            DEFAULT_POLLING_TIME_SECONDS.total_seconds()
            + random.uniform(
                -POLL_JITTER_SECONDS.total_seconds(),
                POLL_JITTER_SECONDS.total_seconds(),
            )
        )
      except KeyboardInterrupt:
        break
    return {
        "result": "success",
        "reason": (
            "The command was interrupted, but the process is still running"
            " in the background."
        ),
    }
