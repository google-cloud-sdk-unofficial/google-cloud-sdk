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
"""Delete environment command."""

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Managed Service for Apache Spark environment."""

  detailed_help = {
      'EXAMPLES': """\
          To delete an environment named `my-env` in `us-central1`, run:

            $ {command} my-env --location=us-central1
          """,
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack(), api_version='v2')
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddTimeoutFlag(parser)
    flags.AddEnvironmentResourceArg(parser, 'delete', dataproc.api_version)

  def Run(self, args):
    environment_ref = args.CONCEPTS.environment.Parse()
    dataproc = dp.Dataproc(
        self.ReleaseTrack(),
        api_version='v2',
        location=environment_ref.locationsId,
    )

    console_io.PromptContinue(
        message="The environment '{0}' will be deleted.".format(
            environment_ref.Name()
        ),
        cancel_on_no=True,
        cancel_string='Deletion canceled by user.',
    )

    request = (
        dataproc.messages.DataprocProjectsLocationsEnvironmentsDeleteRequest(
            name=environment_ref.RelativeName(),
            requestId=util.GetUniqueId(),
        )
    )
    operation = dataproc.client.projects_locations_environments.Delete(request)

    if args.async_:
      log.status.Print(
          'Deleting [{0}] with operation [{1}].'.format(
              environment_ref.RelativeName(), operation.name
          )
      )
      return operation

    operation = util.WaitForOperation(
        dataproc,
        operation,
        message="Waiting for environment '{0}' to delete.".format(
            environment_ref.Name()
        ),
        timeout_s=args.timeout,
    )
    log.DeletedResource(environment_ref.RelativeName())
    return operation
