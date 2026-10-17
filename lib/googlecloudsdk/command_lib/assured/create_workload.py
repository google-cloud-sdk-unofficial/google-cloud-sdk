# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Helpers for creating a new Assured Workloads environment."""

import textwrap

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import message_util
from googlecloudsdk.api_lib.assured import workloads as apis
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': 'Create a new Assured Workloads environment.',
    'EXAMPLES': textwrap.dedent("""\
        The following example command creates a new Assured Workloads environment with these properties:

        * belonging to an organization with ID 123
        * located in the `us-central1` region
        * display name `Test-Workload`
        * compliance regime `FEDRAMP_MODERATE`
        * billing account `billingAccounts/456`
        * first key rotation set for 10:15am on the December 30, 2020
        * key rotation interval set for every 48 hours
        * with the label: key = `LabelKey1`, value = `LabelValue1`
        * with the label: key = `LabelKey2`, value = `LabelValue2`
        * provisioned resources parent `folders/789`
        * with custom project ID `my-custom-id` for consumer project
        * with external identifier for the workload of `external-id`

          $ {command} --organization=123 --location=us-central1 --display-name=Test-Workload --compliance-regime=FEDRAMP_MODERATE --billing-account=billingAccounts/456 --next-rotation-time=2020-12-30T10:15:00.00Z --rotation-period=172800s --labels=LabelKey1=LabelValue1,LabelKey2=LabelValue2 --provisioned-resources-parent=folders/789 --resource-settings=consumer-project-id=my-custom-id --external-identifier=external-id

        The following example command creates a new Partner Assured Workloads, with the following properties:

        * belonging to an organization with ID 123
        * located in the `me-central2` region
        * display name `Test-Workload`
        * partner `CNTXT`
        * partner services billing account `billingAccounts/789`
        * billing account `billingAccounts/456`
        * data logs viewer partner permission enabled
        * first key rotation set for 10:15am on the December 30, 2020
        * key rotation interval set for every 48 hours
        * with the label: key = `LabelKey1`, value = `LabelValue1`
        * with the label: key = `LabelKey2`, value = `LabelValue2`
        * provisioned resources parent `folders/789`
        * with custom project ID `my-custom-id` for consumer project
        * with external identifier for the workload of `external-id`

          $ {command} --organization=123 --location=me-central2 --display-name=Test-Workload --compliance-regime=ASSURED_WORKLOADS_FOR_PARTNERS --partner=SOVEREIGN_CONTROLS_BY_CNTXT --partner-services-billing-account=billingAccounts/01BF3F-2C6DE5-30C607 --partner-permissions=data-logs-viewer=true --billing-account=billingAccounts/456 --next-rotation-time=2020-12-30T10:15:00.00Z --rotation-period=172800s --labels=LabelKey1=LabelValue1,LabelKey2=LabelValue2 --provisioned-resources-parent=folders/789 --resource-settings=consumer-project-id=my-custom-id  --external-identifier=external-id

        The following example command creates a new Assured Workloads environment onboarding an existing project (V2):

        * belonging to an organization with ID 123
        * located in the `us-central1` region
        * description `My Workload`
        * onboarding existing project `projects/456`
        * compliance framework `fedramp-moderate`
        * control configuration specified from file `controls.yaml`

          $ {command} my-workload --organization=123 --location=us-central1 --description="My Workload" --target-project=projects/456 --framework=fedramp-moderate --cloud-control-configs-from-file=controls.yaml --version=v2

        The following example command creates a new Assured Workloads environment provisioning a new project with CMEK (V2):

        * belonging to an organization with ID 123
        * located in the `us-central1` region
        * description `CMEK Workload`
        * provisioning a new project with ID `custom-id` and billing account `billingAccounts/456`
        * compliance framework `il4`
        * KMS key ring `projects/kms-p/locations/us-central1/keyRings/r1`
        * control configuration specified from file `controls.yaml`

          $ {command} --organization=123 --location=us-central1 --description="CMEK Workload" --new-project-config=project_id=custom-id,billing_account=billingAccounts/456 --framework=il4 --cmek-key-ring=projects/kms-p/locations/us-central1/keyRings/r1 --cloud-control-configs-from-file=controls.yaml --version=v2
        """),
}


def RunV1(args, release_track):
  """Run the create command using the V1 API."""
  with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
      release_track=release_track, region=args.location
  ):
    parent = message_util.CreateAssuredParent(
        organization_id=args.organization, location=args.location
    )
    workload = message_util.CreateAssuredWorkload(
        display_name=args.display_name,
        compliance_regime=args.compliance_regime,
        partner=args.partner,
        partner_services_billing_account=args.partner_services_billing_account,
        partner_permissions=args.partner_permissions,
        billing_account=args.billing_account,
        next_rotation_time=args.next_rotation_time,
        rotation_period=args.rotation_period,
        labels=args.labels,
        provisioned_resources_parent=args.provisioned_resources_parent,
        resource_settings=args.resource_settings,
        enable_sovereign_controls=args.enable_sovereign_controls,
        release_track=release_track,
    )
    client = apis.WorkloadsClient(release_track=release_track)
    return client.Create(
        external_id=args.external_identifier,
        parent=parent,
        workload=workload,
    )


def RunV2(args, release_track):
  """Run the create command using the V2 API."""
  with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
      release_track=release_track, region=args.location
  ):
    parent = message_util.CreateAssuredParent(
        organization_id=args.organization, location=args.location
    )
    cmek_config = None
    if args.cmek_key_ring or args.cmek_dedicated_project_config:
      is_folder_target = bool(args.target_folder or args.new_folder_config)
      cmek_config = message_util.BuildCmekConfig(
          key_ring_id=args.cmek_key_ring,
          dedicated_project_dict=args.cmek_dedicated_project_config,
          is_folder_target=is_folder_target,
          release_track=release_track,
      )
    resource_config = message_util.BuildResourceConfig(
        target_project=args.target_project,
        target_folder=args.target_folder,
        new_project_dict=args.new_project_config,
        new_folder_dict=args.new_folder_config,
        release_track=release_track,
    )
    framework = message_util.BuildFrameworkReference(
        framework=args.framework,
        major_revision_id=args.framework_major_revision,
        release_track=release_track,
    )
    control_source = (
        args.cloud_control_configs_from_file or args.cloud_control_config
    )
    cloud_control_configs = []
    if control_source:
      cloud_control_configs = message_util.BuildCloudControlConfigs(
          control_dicts_or_file=control_source,
          release_track=release_track,
      )
    workload = message_util.CreateAssuredWorkloadV2(
        resource_config=resource_config,
        framework=framework,
        cloud_control_configs=cloud_control_configs,
        cmek_config=cmek_config,
        description=args.description,
        release_track=release_track,
    )
    workload_id = (
        args.workload_id or args.flag_workload_id or args.external_identifier
    )
    client = apis.WorkloadsClient(release_track=release_track, api_version='v2')
    is_async = args.async_
    if is_async:
      created_resource = client.CreateAsyncV2(
          parent=parent,
          workload=workload,
          workload_id=workload_id,
      )
    else:
      created_resource = client.CreateV2(
          parent=parent,
          workload=workload,
          workload_id=workload_id,
      )
    return created_resource, is_async


def Epilog(created_resource, is_async):
  """Displays resource creation message upon command completion."""
  if created_resource and hasattr(created_resource, 'name'):
    log.CreatedResource(
        created_resource.name,
        kind='Assured Workloads environment',
        is_async=is_async,
    )
