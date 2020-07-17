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
"""Implements command to create a new guest policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy as agent_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import guest_policy_to_ops_agents_policy_converter as to_ops_agents
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import ops_agents_policy_to_guest_policy_converter as to_guest_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents.validators import ops_agents_policy_validator as validator
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances.ops_agents.policies import parser_utils
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Create a policy that manages Google Cloud Operations Suite agents across Google Cloud Compute instances."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To create a guest policy ``policy1'' in the current project, run:

            $ {command} policy1 --project=my-project --os-types=short-name=centos,version=7 --description="A test policy to install agents" --agents="type=logging,version=1.x.x,enable-autoupgrade=true,package-state=installed;type=metrics,version=6.x.x,enable-autoupgrade=false,package-state=installed" --instances=zones/us-central1-a/instances/test-instance-1,zones/us-central1-a/instances/test-instance-2 --group-labels="env=prod,product=myproduct;env=staging,product=myproduct" --zones="us-central1-a,us-central1-b"
          """,
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    parser_utils.AddSharedArgs(parser)
    parser_utils.AddMutationArgs(parser)

  def Run(self, args):
    """See base class."""

    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(
        release_track, api_version_override='v1beta')
    messages = osconfig_api_utils.GetClientMessages(
        release_track, api_version_override='v1beta')
    ops_agents_policy = agent_policy.CreateOpsAgentPolicy(
        args.description, args.agents, args.group_labels, args.os_types,
        args.zones, args.instances)
    validator.ValidateOpsAgentsPolicy(ops_agents_policy)
    guest_policy = to_guest_policy.ConvertOpsAgentPolicyToGuestPolicy(
        messages, ops_agents_policy)
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
        complete_guest_policy)
    return ops_agents_policy
