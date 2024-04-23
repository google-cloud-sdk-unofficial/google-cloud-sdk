# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

# pylint: disable=line-too-long
"""Implements command to create an ops agents policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute.instances.ops_agents import cloud_ops_agents_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy as agent_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import cloud_ops_agents_policy_to_os_assignment_policy_converter as to_os_policy_assignment
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import guest_policy_to_ops_agents_policy_converter as to_ops_agents
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import ops_agents_policy_to_guest_policy_converter as to_guest_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import os_policy_assignment_to_cloud_ops_agents_policy_converter as to_cloud_ops_agents
from googlecloudsdk.api_lib.compute.instances.ops_agents.validators import ops_agents_policy_validator as validator
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances.ops_agents.policies import parser_utils
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.generated_clients.apis.osconfig.v1 import osconfig_v1_messages as osconfig


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateOsConfig(base.Command):
  """Create a Google Cloud's operations suite agents (Ops Agents) policy.

  *{command}* creates a policy that facilitates agent management across
  Compute Engine instances based on user specified instance filters. This policy
  installs, specifies versioning, enables autoupgrade, and removes Ops Agents.

  The command returns the content of the created policy or an error indicating
  why the creation fails. The created policy takes effect asynchronously. It
  can take 10-15 minutes for the VMs to enforce the newly created policy.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To create a policy named ``ops-agents-test-policy'' that targets a
          single CentOS 7 VM instance named
          ``zones/us-central1-a/instances/test-instance'' for testing or
          development and installs both Logging and Monitoring Agents on that
          VM instance, run:

            $ {command} ops-agents-test-policy --agent-rules="type=logging,enable-autoupgrade=false;type=metrics,enable-autoupgrade=false" --description="A test policy." --os-types=short-name=centos,version=7 --instances=zones/us-central1-a/instances/test-instance

          To create a policy named ``ops-agents-prod-policy'' that targets all
          CentOS 7 VMs in zone ``us-central1-a'' with either
          ``env=prod,product=myapp'' or ``env=staging,product=myapp'' labels
          and makes sure the logging agent and metrics agent versions are pinned
          to specific major versions for staging and production, run:

          $ {command} ops-agents-prod-policy --agent-rules="type=logging,version=1.*.*,enable-autoupgrade=false;type=metrics,version=6.*.*,enable-autoupgrade=false" --description="A prod policy." --os-types=short-name=centos,version=7 --zones=us-central1-a --group-labels="env=prod,product=myapp;env=staging,product=myapp"

          To create a policy named ``ops-agents-prod-policy'' that targets all
          CentOS 7 VMs in zone ``us-central1-a'' with either
          ``env=prod,product=myapp'' or ``env=staging,product=myapp'' labels
          and makes sure the ops-agent version is pinned
          to specific major versions for staging and production, run:

          $ {command} ops-agents-prod-policy --agent-rules="type=ops-agent,version=1.*.*,enable-autoupgrade=false" --description="A prod policy." --os-types=short-name=centos,version=7 --zones=us-central1-a --group-labels="env=prod,product=myapp;env=staging,product=myapp"
          """,
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    parser_utils.AddSharedArgs(parser)
    parser_utils.AddMutationArgs(parser)
    parser_utils.AddCreateArgs(parser)

  def Run(self, args):
    """See base class."""

    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(
        release_track, api_version_override='v1beta'
    )
    messages = osconfig_api_utils.GetClientMessages(
        release_track, api_version_override='v1beta'
    )
    ops_agents_policy = agent_policy.CreateOpsAgentPolicy(
        args.description,
        args.agent_rules,
        args.group_labels,
        args.os_types,
        args.zones,
        args.instances,
    )
    validator.ValidateOpsAgentsPolicy(ops_agents_policy)
    guest_policy = to_guest_policy.ConvertOpsAgentPolicyToGuestPolicy(
        messages, ops_agents_policy
    )
    project = properties.VALUES.core.project.GetOrFail()
    parent_path = osconfig_command_utils.GetProjectUriPath(project)
    request = messages.OsconfigProjectsGuestPoliciesCreateRequest(
        guestPolicy=guest_policy,
        guestPolicyId=args.POLICY_ID,
        parent=parent_path,
    )
    service = client.projects_guestPolicies
    complete_guest_policy = service.Create(request)
    ops_agents_policy = to_ops_agents.ConvertGuestPolicyToOpsAgentPolicy(
        complete_guest_policy
    )
    return ops_agents_policy


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  """Create a Google Cloud's operations suite agents (Ops Agents) policy.

  TBD
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          TBD
          """,
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    parser.add_argument(
        'POLICY_ID',
        type=str,
        help="""\
          ID of the policy.

          This ID must contain only lowercase letters,
          numbers, and hyphens, end with a number or a letter, be between 1-63
          characters, and be unique within the project.
          """,
    )
    parser.add_argument(
        '--file',
        required=True,
        help="""\
          The YAML file with the Cloud Ops Policy Assignment to create. For
          information about the Cloud Ops Policy Assignment format, see [PLACEHOLDER for our public doc].""",
    )
    parser.add_argument(
        '--zone',
        required=True,
        help="""\
          this is zone.""",
    )

  def Run(self, args):
    """See base class."""

    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    # Load config from yaml file.
    config = yaml.load_path(args.file)

    # Convert to domain object from users input.
    ops_agents_policy = cloud_ops_agents_policy.CreateOpsAgentsPolicy(config)

    project = properties.VALUES.core.project.GetOrFail()
    parent_path = osconfig_command_utils.GetProjectLocationUriPath(
        project, args.zone
    )

    name = f'{parent_path}/osPolicyAssignments/{args.POLICY_ID}'

    ops_policy_assignment = (
        to_os_policy_assignment.ConvertOpsAgentsPolicyToOSPolicyAssignment(
            name, ops_agents_policy
        )
    )

    # Create request to projects_locations_osPolicyAssignments.
    request = (
        messages.OsconfigProjectsLocationsOsPolicyAssignmentsCreateRequest(
            oSPolicyAssignment=ops_policy_assignment,
            osPolicyAssignmentId=args.POLICY_ID,
            parent=parent_path,
        )
    )
    service = client.projects_locations_osPolicyAssignments
    response = service.Create(request)
    # Converting response from JSON python object.
    complete_os_policy_assignment_obj = encoding.MessageToPyValue(
        response.response
    )
    complete_os_policy_assignment = encoding.PyValueToMessage(
        osconfig.OSPolicyAssignment, complete_os_policy_assignment_obj
    )
    # TODO: b/334112329 - Fix yaml marshaling
    policy = to_cloud_ops_agents.ConvertOsPolicyAssignmentToCloudOpsAgentPolicy(
        complete_os_policy_assignment
    )

    return policy
