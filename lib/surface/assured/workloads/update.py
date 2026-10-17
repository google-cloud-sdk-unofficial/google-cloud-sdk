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
"""Command to update an Assured Workload."""

import textwrap
from typing import Any

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import message_util
from googlecloudsdk.api_lib.assured import workloads as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.assured import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': 'Update a given Assured Workloads environment.',
    'EXAMPLES': textwrap.dedent("""\
        To update the display name and labels of a V1 Assured Workload using a
        full resource name:

          $ {command} organizations/123/locations/us-central1/workloads/456 \\
              --display-name=Test-Workload-2 \\
              --labels=dept=sec,env=prod \\
              --etag=789

        To update a V1 Assured Workload using discrete resource flags:

          $ {command} 456 --organization=123 --location=us-central1 \\
              --display-name=Test-Workload-2 --etag=789

        To update the major revision and cloud control configurations of a V2
        Assured Workload using a full resource name:

          $ {command} organizations/123/locations/us-central1/workloads/456 \\
              --framework-major-revision=2 \\
              --cloud-control-configs-from-file=/path/to/controls.yaml \\
              --version=v2

        To update the major revision and cloud control configurations of a V2
        Assured Workload using discrete resource flags:

          $ {command} 456 --organization=123 --location=us-central1 \\
              --framework-major-revision=2 \\
              --cloud-control-configs-from-file=/path/to/controls.yaml \\
              --version=v2

        To update cloud control configurations from a file for a V2 Assured
        Workload:

          $ {command} 456 --organization=123 --location=us-central1 \\
              --cloud-control-configs-from-file=/path/to/controls.yaml \\
              --version=v2

        To update a V2 Assured Workload asynchronously:

          $ {command} 456 --organization=123 --location=us-central1 \\
              --framework-major-revision=2 \\
              --cloud-control-configs-from-file=/path/to/controls.yaml \\
              --async --version=v2
        """),
}


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
@base.DefaultUniverseOnly
class Update(base.UpdateCommand):
  """Update Assured Workloads environments."""

  detailed_help = _DETAILED_HELP

  updated_resource: Any = None
  _is_async: bool = False

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    """Register flags for this command."""
    flags.AddUnifiedUpdateWorkloadFlags(parser)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    """Run the update command."""
    flags.ValidateUpdateWorkloadVersionFlags(args)
    workload_resource = args.CONCEPTS.workload.Parse()
    region = workload_resource.Parent().Name()
    workload_name = workload_resource.RelativeName()
    version = flags.GetApiVersion(args, release_track=self.ReleaseTrack())
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=region
    ):
      if version == 'v2':
        cloud_control_configs = None
        if args.IsKnownAndSpecified('cloud_control_config'):
          cloud_control_configs = message_util.BuildCloudControlConfigs(
              args.cloud_control_config, release_track=self.ReleaseTrack()
          )
        elif args.IsKnownAndSpecified('cloud_control_configs_from_file'):
          cloud_control_configs = message_util.BuildCloudControlConfigs(
              args.cloud_control_configs_from_file,
              release_track=self.ReleaseTrack(),
          )

        update_mask = message_util.CreateUpdateMaskV2(
            framework_major_revision_id=(
                args.framework_major_revision
                if args.IsKnownAndSpecified('framework_major_revision')
                else None
            ),
            cloud_control_configs=cloud_control_configs,
        )

        workload = message_util.CreateAssuredWorkloadForUpdateV2(
            framework_major_revision_id=(
                args.framework_major_revision
                if args.IsKnownAndSpecified('framework_major_revision')
                else None
            ),
            cloud_control_configs=cloud_control_configs,
            etag=args.etag if args.IsKnownAndSpecified('etag') else None,
            release_track=self.ReleaseTrack(),
        )

        client = apis.WorkloadsClient(
            release_track=self.ReleaseTrack(), api_version='v2'
        )
        self._is_async = args.IsKnownAndSpecified('async_') and args.async_
        if self._is_async:
          self.updated_resource = client.UpdateAsyncV2(
              name=workload_name,
              workload=workload,
              update_mask=update_mask,
          )
        else:
          self.updated_resource = client.UpdateV2(
              name=workload_name,
              workload=workload,
              update_mask=update_mask,
          )
        return self.updated_resource

      update_mask = message_util.CreateUpdateMask(
          args.display_name
          if args.IsKnownAndSpecified('display_name')
          else None,
          args.labels if args.IsKnownAndSpecified('labels') else None,
          args.violation_notifications_enabled
          if args.IsKnownAndSpecified('violation_notifications_enabled')
          else None,
      )
      workload = message_util.CreateAssuredWorkload(
          display_name=(
              args.display_name
              if args.IsKnownAndSpecified('display_name')
              else None
          ),
          labels=args.labels if args.IsKnownAndSpecified('labels') else None,
          etag=args.etag if args.IsKnownAndSpecified('etag') else None,
          violation_notifications_enabled=(
              args.violation_notifications_enabled
              if args.IsKnownAndSpecified('violation_notifications_enabled')
              else None
          ),
          release_track=self.ReleaseTrack(),
      )
      client = apis.WorkloadsClient(release_track=self.ReleaseTrack())
      self._is_async = False
      self.updated_resource = client.Update(
          workload=workload, name=workload_name, update_mask=update_mask
      )
      return self.updated_resource

  def Epilog(self, resources_were_displayed: bool) -> None:
    """Displays resource update message upon command completion."""
    if self.updated_resource:
      if hasattr(self.updated_resource, 'name'):
        log.UpdatedResource(
            self.updated_resource.name,
            kind='Assured Workloads environment',
            is_async=self._is_async,
        )
