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
"""Import environment command."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc.environments import util as env_util
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Import(base.Command):
  """Import a Managed Service for Apache Spark environment.

  If the environment doesn't exist, it is created from the imported
  configuration. Otherwise, its configuration is replaced by the imported
  configuration, which builds a new revision of the environment. Fields that
  are missing from the imported configuration are cleared. If the imported
  configuration sets neither `baseVersion` nor `baseEnvironment`, the existing
  base is kept.

  To edit an existing environment, export it to a file, edit the file, and
  then import the file.
  """

  detailed_help = {
      'EXAMPLES': """\
          To create or replace environment `my-env` in `us-central1` from a
          file named `my-env.yaml`, run:

            $ {command} my-env --location=us-central1 --source=my-env.yaml
          """,
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack(), api_version='v2')
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddTimeoutFlag(parser, default='35m')
    flags.AddEnvironmentResourceArg(parser, 'import', dataproc.api_version)
    export_util.AddImportFlags(parser)

  def Run(self, args):
    environment_ref = args.CONCEPTS.environment.Parse()
    dataproc = dp.Dataproc(
        self.ReleaseTrack(),
        api_version='v2',
        location=environment_ref.locationsId,
    )
    environment = env_util.ReadEnvironment(
        dataproc, args.source, environment_ref
    )

    # Look up the environment instead of trying to create it first: the service
    # validates create requests before it checks whether the environment
    # exists, so creating an existing environment doesn't always fail with
    # ALREADY_EXISTS.
    try:
      dataproc.client.projects_locations_environments.Get(
          dataproc.messages.DataprocProjectsLocationsEnvironmentsGetRequest(
              name=environment_ref.RelativeName()
          )
      )
    except apitools_exceptions.HttpNotFoundError:
      return env_util.CreateEnvironment(
          dataproc, environment_ref, environment, args
      )

    console_io.PromptContinue(
        message=(
            "The environment '{0}' already exists and will be overwritten."
        ).format(environment_ref.Name()),
        cancel_on_no=True,
        cancel_string='Import canceled by user.',
    )
    return env_util.UpdateEnvironment(
        dataproc,
        environment_ref,
        environment,
        env_util.GetImportUpdateMask(environment),
        args,
    )
