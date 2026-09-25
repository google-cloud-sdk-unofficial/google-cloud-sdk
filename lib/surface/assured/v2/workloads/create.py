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
"""Command to create a new Assured Workloads V2 environment."""

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import message_util
from googlecloudsdk.api_lib.assured import workloads as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': 'Create a new Assured Workloads V2 environment.',
    'EXAMPLES': (
        """\
        To create an Assured Workload onboarding an existing project:

          $ {command} my-workload --organization=123 --location=us-central1 --description="My Workload" --target-project=projects/456 --framework=fedramp-moderate

        To create an Assured Workload provisioning a new project with CMEK:

          $ {command} --organization=123 --location=us-central1 --description="CMEK Workload" --new-project-config=project_id=custom-id,billing_account=billingAccounts/456 --framework=il4 --cmek-key-ring=projects/kms-p/locations/us-central1/keyRings/r1
        """
    ),
}


@base.ReleaseTracks(ReleaseTrack.GA, ReleaseTrack.BETA, ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Create(base.CreateCommand):
  """Create a new Assured Workloads V2 environment."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddCreateWorkloadV2Flags(parser)

  def Run(self, args):
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=args.location
    ):
      parent = 'organizations/{org_id}/locations/{location}'.format(
          org_id=args.organization, location=args.location
      )
      cmek_config = None
      if args.cmek_key_ring or args.cmek_dedicated_project_config:
        is_folder_target = bool(args.target_folder or args.new_folder_config)
        cmek_config = message_util.BuildCmekConfig(
            key_ring_id=args.cmek_key_ring,
            dedicated_project_dict=args.cmek_dedicated_project_config,
            is_folder_target=is_folder_target,
            release_track=self.ReleaseTrack(),
        )
      resource_config = message_util.BuildResourceConfig(
          target_project=args.target_project,
          target_folder=args.target_folder,
          new_project_dict=args.new_project_config,
          new_folder_dict=args.new_folder_config,
          release_track=self.ReleaseTrack(),
      )
      framework = message_util.BuildFrameworkReference(
          framework=args.framework,
          major_revision_id=args.framework_major_revision,
          release_track=self.ReleaseTrack(),
      )
      control_source = (
          args.cloud_control_configs_from_file or args.cloud_control_config
      )
      cloud_control_configs = []
      if control_source:
        cloud_control_configs = message_util.BuildCloudControlConfigs(
            control_dicts_or_file=control_source,
            release_track=self.ReleaseTrack(),
        )
      workload = message_util.CreateAssuredWorkloadV2(
          resource_config=resource_config,
          framework=framework,
          cloud_control_configs=cloud_control_configs,
          cmek_config=cmek_config,
          description=args.description,
          release_track=self.ReleaseTrack(),
      )
      workload_id = (
          args.workload_id or args.flag_workload_id or args.external_identifier
      )
      client = apis.WorkloadsClient(
          release_track=self.ReleaseTrack(), api_version='v2'
      )
      self.is_async = args.async_
      if args.async_:
        self.created_resource = client.CreateAsyncV2(
            parent=parent,
            workload=workload,
            workload_id=workload_id,
        )
      else:
        self.created_resource = client.CreateV2(
            parent=parent,
            workload=workload,
            workload_id=workload_id,
        )
      return self.created_resource

  def Epilog(self, resources_were_displayed):
    resource = getattr(self, 'created_resource', None)
    if resource and hasattr(resource, 'name'):
      log.CreatedResource(
          resource.name,
          kind='Assured Workloads environment',
          is_async=getattr(self, 'is_async', False),
      )
