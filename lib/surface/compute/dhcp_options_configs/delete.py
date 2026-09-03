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
"""Command for deleting DHCP options configs."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.dhcp_options_configs import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete Google Compute Engine DHCP options configurations."""

  detailed_help = {
      'brief': 'Delete Google Compute Engine DHCP options configurations.',
      'DESCRIPTION': (
          """\
      *{command}* is used to delete regional DHCP options configurations.
      """
      ),
      'EXAMPLES': (
          """\
      To delete a DHCP options config in region us-central1, run:

        $ {command} my-dhcp-config --region=us-central1
      """
      ),
  }

  DHCP_OPTIONS_CONFIG_ARG = None

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    cls.DHCP_OPTIONS_CONFIG_ARG = flags.DhcpOptionsConfigArgument(plural=True)
    cls.DHCP_OPTIONS_CONFIG_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.DhcpOptionsConfigsCompleter)

  def Run(self, args):
    """Issue a DhcpOptionsConfig DELETE request."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    dhcp_config_refs = self.DHCP_OPTIONS_CONFIG_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.REGION
    )
    utils.PromptForDeletion(dhcp_config_refs)

    requests = []
    for ref in dhcp_config_refs:
      request = client.messages.ComputeDhcpOptionsConfigsDeleteRequest(
          project=ref.project, region=ref.region, dhcpOptionsConfig=ref.Name()
      )
      requests.append(
          (client.apitools_client.dhcpOptionsConfigs, 'Delete', request)
      )

    return client.MakeRequests(requests)
