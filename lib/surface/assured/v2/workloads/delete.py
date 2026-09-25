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
"""Command to delete an Assured Workloads V2 environment."""

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
    'DESCRIPTION': 'Delete an Assured Workload.',
    'EXAMPLES': (
        """\
        To delete an Assured Workload in the us-central1 region belonging to an
        organization with ID 123 and workload ID 456, run:

          $ {command} organizations/123/locations/us-central1/workloads/456

        To delete asynchronously without waiting for the operation to complete:

          $ {command} organizations/123/locations/us-central1/workloads/456 --async
        """
    ),
}


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
@base.DefaultUniverseOnly
class Delete(base.DeleteCommand):
  """Delete an Assured Workload."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    flags.AddDeleteWorkloadV2Flags(parser)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    workload_resource = args.CONCEPTS.workload.Parse()
    region = workload_resource.Parent().Name()
    workload = workload_resource.RelativeName()

    if not console_io.PromptContinue(
        message='You are about to delete Workload [{}]'.format(workload),
        default=True,
    ):
      log.status.Print('Aborted by user.')
      return None

    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=region
    ):
      client = apis.WorkloadsClient(
          release_track=self.ReleaseTrack(), api_version='v2'
      )
      self._resource_name = workload
      self._is_async = args.async_
      if self._is_async:
        return client.DeleteAsyncV2(name=workload, etag=args.etag)
      return client.DeleteV2(name=workload, etag=args.etag)

  def Epilog(self, resources_were_displayed: bool) -> None:
    if hasattr(self, '_resource_name') and self._resource_name:
      log.DeletedResource(
          self._resource_name,
          kind='Assured Workloads environment',
          is_async=getattr(self, '_is_async', False),
      )
