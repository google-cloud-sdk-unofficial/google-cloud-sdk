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
"""Command for describing DHCP options configs."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.dhcp_options_configs import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe a Google Compute Engine DHCP options configuration."""

  detailed_help = {
      'brief': 'Describe a Google Compute Engine DHCP options configuration.',
      'DESCRIPTION': (
          """\
      *{command}* displays all data associated with a regional DHCP options configuration.
      """
      ),
      'EXAMPLES': (
          """\
      To describe a DHCP options config in region us-central1, run:

        $ {command} my-dhcp-config --region=us-central1
      """
      ),
  }

  DHCP_OPTIONS_CONFIG_ARG = None

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    cls.DHCP_OPTIONS_CONFIG_ARG = flags.DhcpOptionsConfigArgument()
    cls.DHCP_OPTIONS_CONFIG_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    """Issue a DhcpOptionsConfig GET request."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    dhcp_config_ref = self.DHCP_OPTIONS_CONFIG_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.REGION
    )

    request = client.messages.ComputeDhcpOptionsConfigsGetRequest(
        project=dhcp_config_ref.project,
        region=dhcp_config_ref.region,
        dhcpOptionsConfig=dhcp_config_ref.Name(),
    )

    return client.MakeRequests(
        [(client.apitools_client.dhcpOptionsConfigs, 'Get', request)]
    )[0]
