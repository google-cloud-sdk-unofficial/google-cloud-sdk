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
"""Delete command for orchestration pipelines."""

import time

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.composer import dags_util
from googlecloudsdk.api_lib.composer import environments_util
from googlecloudsdk.api_lib.composer import util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.orchestration_pipelines.tools import composer_utils
from googlecloudsdk.command_lib.orchestration_pipelines.tools import gcs_utils
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

WAIT_TIMEOUT_SECONDS = 300


@calliope_base.DefaultUniverseOnly
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class Delete(calliope_base.DeleteCommand):
  """Delete a pipelines bundle from a runner."""

  @staticmethod
  def Args(parser):
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--environment',
        help=(
            'The target environment of the pipeline, as defined in'
            ' deployment.yaml.'
        ),
    )
    group.add_argument(
        '--runner',
        help=(
            'The full resource name of the runner to '
            'delete a pipeline from.'
        ),
    )
    parser.add_argument(
        '--bundle',
        required=True,
        help='The ID of the bundle to delete.',
    )
    yaml_processor.add_substitution_flags(parser)

  def _DeleteObjectsWithPrefix(
      self, storage_client, bucket, bucket_ref, prefix
  ):
    log.status.Print(f'Deleting objects with prefix: gs://{bucket}/{prefix}')
    found_any = False
    for obj in storage_client.ListBucket(bucket_ref, prefix=prefix):
      found_any = True
      obj_ref = storage_util.ObjectReference.FromName(bucket, obj.name)
      try:
        storage_client.DeleteObject(obj_ref)
      except api_exceptions.HttpError as e:
        log.warning(f'Failed to delete {obj.name}: {e}')

    if not found_any:
      log.status.Print(
          f'No objects found with prefix: gs://{bucket}/{prefix}'
      )

  def _WaitForDagsRemoval(self, env_ref, bundle_id):
    list_filter = composer_utils.build_dags_filter_tags(bundle=bundle_id)
    log.status.Print(
        f"Waiting for pipelines in bundle '{bundle_id}' to be deleted..."
    )
    start_time = time.time()
    while time.time() - start_time < WAIT_TIMEOUT_SECONDS:
      dags = dags_util.ListDags(env_ref, list_filter=list_filter)
      if not dags:
        return
      composer_utils.sleep_with_jitter()
    log.warning(
        f"Timeout waiting for pipelines in bundle '{bundle_id}' to be deleted."
        ' Proceeding with data deletion.'
    )

  def Run(self, args):
    api_version = util.GetApiVersion(self.ReleaseTrack())

    if args.runner:
      env_model = None
    else:
      env_model = yaml_processor.load_environment_with_args(args)

    environment_resource_name = composer_utils.build_resource_name(
        env_model, args.runner
    )
    env_ref = resources.REGISTRY.ParseRelativeName(
        environment_resource_name,
        collection='composer.projects.locations.environments',
        api_version=api_version,
    )
    env_obj = environments_util.Get(env_ref, release_track=self.ReleaseTrack())

    if not env_obj.config or not env_obj.config.dagGcsPrefix:
      raise gcs_utils.GcsError(
          'Failed to retrieve GCS bucket from Composer environment'
          f' {env_ref.Name()}.'
      )
    bucket = env_obj.config.dagGcsPrefix.replace('gs://', '').split('/')[0]

    bundle_id = args.bundle
    storage_client = storage_api.StorageClient()

    dags_prefix = (
        f'{gcs_utils.ORCHESTRATION_PIPELINES_DAGS_DIRECTORY}/{bundle_id}/'
    )
    data_prefix = (
        f'{gcs_utils.ORCHESTRATION_PIPELINES_DATA_DIRECTORY}/{bundle_id}/'
    )

    log.status.Print(f"Deleting bundle '{bundle_id}' from bucket '{bucket}'...")

    bucket_ref = storage_util.BucketReference(bucket)
    self._DeleteObjectsWithPrefix(
        storage_client, bucket, bucket_ref, dags_prefix
    )
    self._WaitForDagsRemoval(env_ref, bundle_id)
    self._DeleteObjectsWithPrefix(
        storage_client, bucket, bucket_ref, data_prefix
    )

    log.status.Print(f"Successfully deleted bundle '{bundle_id}'.")
    return {'result': 'success'}
