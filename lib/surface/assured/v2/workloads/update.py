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
"""Command to update an Assured Workloads V2 environment."""

import textwrap
from typing import Any
from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import message_util
from googlecloudsdk.api_lib.assured import workloads as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': 'Update a given Assured Workloads V2 environment.',
    'EXAMPLES': textwrap.dedent("""\
        To update the description of an Assured Workloads V2 environment in the
        us-central1 region belonging to an organization with ID 123 and
        workload ID 456, run:

          $ {command} organizations/123/locations/us-central1/workloads/456 --description="Updated description"

        To update the cloud control configs from a YAML file, run:

          $ {command} organizations/123/locations/us-central1/workloads/456 --cloud-control-configs-from-file=/path/to/controls.yaml
        """),
}


@base.ReleaseTracks(ReleaseTrack.GA, ReleaseTrack.BETA, ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Update(base.UpdateCommand):
  """Update Assured Workloads V2 environments."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    """See base class."""
    flags.AddUpdateWorkloadV2Flags(parser)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    """Run the update command."""
    workload_resource = args.CONCEPTS.workload.Parse()
    region = workload_resource.Parent().Name()
    workload_name = workload_resource.RelativeName()

    cloud_control_configs = None
    if args.IsSpecified('cloud_control_config'):
      cloud_control_configs = message_util.BuildCloudControlConfigs(
          args.cloud_control_config, release_track=self.ReleaseTrack()
      )
    elif args.IsSpecified('cloud_control_configs_from_file'):
      cloud_control_configs = message_util.BuildCloudControlConfigs(
          args.cloud_control_configs_from_file,
          release_track=self.ReleaseTrack(),
      )

    update_mask = message_util.CreateUpdateMaskV2(
        description=(
            args.description if args.IsSpecified('description') else None
        ),
        cloud_control_configs=cloud_control_configs,
    )

    workload = message_util.CreateAssuredWorkloadForUpdateV2(
        description=(
            args.description if args.IsSpecified('description') else None
        ),
        cloud_control_configs=cloud_control_configs,
        etag=args.etag,
        release_track=self.ReleaseTrack(),
    )

    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=region
    ):
      client = apis.WorkloadsClient(
          release_track=self.ReleaseTrack(), api_version='v2'
      )
      self._is_async = args.async_
      if args.async_:
        self._updated_resource = client.UpdateAsyncV2(
            name=workload_name,
            workload=workload,
            update_mask=update_mask,
        )
      else:
        self._updated_resource = client.UpdateV2(
            name=workload_name,
            workload=workload,
            update_mask=update_mask,
        )
      return self._updated_resource

  def Epilog(self, resources_were_displayed: bool) -> None:
    """See base class."""
    if hasattr(self, '_updated_resource') and self._updated_resource:
      if hasattr(self._updated_resource, 'name'):
        log.UpdatedResource(
            self._updated_resource.name,
            kind='Assured Workloads environment',
            is_async=getattr(self, '_is_async', False),
        )
