# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to delete an existing Assured Workload."""

import textwrap
from typing import Any

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import workloads as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.assured import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

_DETAILED_HELP = {
    'DESCRIPTION': 'Delete a given Assured Workloads environment.',
    'EXAMPLES': textwrap.dedent("""\
        To delete a V1 Assured Workload using a full resource name:

          $ {command} organizations/123/locations/us-central1/workloads/456 \\
              --etag=789

        To delete a V1 Assured Workload using discrete resource flags:

          $ {command} 456 --organization=123 --location=us-central1 --etag=789

        To delete a V2 Assured Workload using a full resource name:

          $ {command} organizations/123/locations/us-central1/workloads/456 \\
              --version=v2

        To delete a V2 Assured Workload using discrete resource flags:

          $ {command} 456 --organization=123 --location=us-central1 --version=v2

        To delete a V2 Assured Workload asynchronously:

          $ {command} 456 --organization=123 --location=us-central1 --async \\
              --version=v2
        """),
}


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
@base.DefaultUniverseOnly
class Delete(base.DeleteCommand):
  """Delete Assured Workloads environment."""

  detailed_help = _DETAILED_HELP

  resource_name: str | None = None
  _is_async: bool = False

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    """Register flags for this command."""
    flags.AddUnifiedDeleteWorkloadFlags(parser)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    """Run the delete command."""
    flags.ValidateDeleteWorkloadVersionFlags(args)
    workload_resource = args.CONCEPTS.workload.Parse()
    region = workload_resource.Parent().Name()
    workload = workload_resource.RelativeName()

    if not console_io.PromptContinue(
        message='You are about to delete Workload [{}]'.format(workload),
        default=True,
    ):
      log.status.Print('Aborted by user.')
      return None

    version = flags.GetApiVersion(args, release_track=self.ReleaseTrack())
    etag = args.etag if args.IsKnownAndSpecified('etag') else None
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=region
    ):
      self.resource_name = workload
      if version == 'v2':
        client = apis.WorkloadsClient(
            release_track=self.ReleaseTrack(), api_version='v2'
        )
        self._is_async = args.IsKnownAndSpecified('async_') and args.async_
        if self._is_async:
          return client.DeleteAsyncV2(name=workload, etag=etag)
        return client.DeleteV2(name=workload, etag=etag)

      client = apis.WorkloadsClient(release_track=self.ReleaseTrack())
      self._is_async = False
      return client.Delete(name=self.resource_name, etag=etag)

  def Epilog(self, resources_were_displayed: bool) -> None:
    """Displays resource deletion message upon command completion."""
    if self.resource_name:
      log.DeletedResource(
          self.resource_name,
          kind='Assured Workloads environment',
          is_async=self._is_async,
      )
