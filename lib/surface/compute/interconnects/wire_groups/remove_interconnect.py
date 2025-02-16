# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Command for adding interconnects to a wire group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects.wire_groups import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.interconnects.cross_site_networks import flags as cross_site_network_flags
from googlecloudsdk.command_lib.compute.interconnects.wire_groups import flags
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION': """\
        *{command}* is used to remove interconnects from a wire group endpoint.

        For an example, refer to the *EXAMPLES* section below.
        """,
    # pylint: disable=line-too-long
    'EXAMPLES': """\
        To remove an interconnect example-interconnect from wire group example-wire-group, run:

          $ {command} example-wire-group --project=example-project --cross-site-network=example-cross-site-network --endpoint-label=example-endpoint --interconnect-label=example-interconnect
        """,
    # pylint: enable=line-too-long
}


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveInterconnect(base.UpdateCommand):
  """Remove interconnect to a Compute Engine wire group.

  *{command}* removes interconnect from a Compute Engine Wire Group endpoint.
  """

  WIRE_GROUP_ARG = None
  CROSS_SITE_NETWORK_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.CROSS_SITE_NETWORK_ARG = (
        cross_site_network_flags.CrossSiteNetworkArgumentForOtherResource()
    )
    cls.CROSS_SITE_NETWORK_ARG.AddArgument(parser)
    cls.WIRE_GROUP_ARG = flags.WireGroupArgument(plural=False)
    cls.WIRE_GROUP_ARG.AddArgument(parser, operation_type='update')
    flags.AddEndpointLabel(parser)
    flags.AddInterconnectLabel(parser)

  def Collection(self):
    return 'compute.wireGroups'

  def Run(self, args):
    """Runs the remove-interconnect command.

    Modifies the existing endpoints and their interconnects. We need to break
    down the endpoints and interconnects to make it easier to add or update the
    interconnects. Since they are nested resources of a WireGroup, it can get
    tricky to do modifications.

    Args:
      args: Object containing CLI parameter values
    Returns:
      Result of running the request.

    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.WIRE_GROUP_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.GLOBAL,
        additional_params={'crossSiteNetwork': args.cross_site_network},
    )
    project = properties.VALUES.core.project.GetOrFail()

    self._messages = holder.client.messages

    wire_group = client.WireGroup(
        ref=ref,
        project=project,
        cross_site_network=args.cross_site_network,
        compute_client=holder.client,
        resources=holder.resources,
    )
    endpoint_label = args.endpoint_label
    interconnect_label = args.interconnect_label
    endpoints = wire_group.Describe().endpoints

    # Convert the endpoints into a map for easier access to the interconnets.
    endpoints_map = self._convert_endpoints_to_dict(endpoints)

    if endpoint_label not in endpoints_map:
      return AttributeError('Endpoint not found.')

    if endpoint_label in endpoints_map:
      interconnects = endpoints_map[endpoint_label].interconnects

      # Convert the interconnects into a map for easier access to the
      # attributes.
      interconnects_map = self._convert_interconnects_to_dict(interconnects)

      # Delete interconnect from the map if it exists.
      if interconnect_label in interconnects_map:
        del interconnects_map[interconnect_label]

      # Rebuild the Interconnect messages
      interconnects = self._build_interconnect_messages(interconnects_map)

      endpoints_map[endpoint_label] = self._messages.WireGroupEndpoint(
          interconnects=interconnects
      )

    endpoints = self._build_endpoint_messages(endpoints_map)

    return wire_group.Patch(
        endpoints=endpoints,
    )

  def _convert_interconnects_to_dict(self, interconnects):
    """Extracts key value pairs from additionalProperties attribute.

    Creates a dict to be able to pass them into the client.

    Args:
      interconnects: the list of interconnect additionalProperties messages

    Returns:
      dictionary containing key value pairs
    """
    interconnects_map = {}

    if not interconnects or not interconnects.additionalProperties:
      return interconnects_map

    for interconnect_property in interconnects.additionalProperties:
      key, value = interconnect_property.key, interconnect_property.value
      interconnects_map[key] = value

    return interconnects_map

  def _convert_endpoints_to_dict(self, endpoints):
    """Extracts the key,value pairs from the additionalProperties attribute.

    Creates a python dict to be able to pass them into the client.

    Args:
      endpoints: the list of additionalProperties messages

    Returns:
      Python dictionary containg the key value pairs.
    """
    endpoints_map = {}

    if not endpoints or not endpoints.additionalProperties:
      return endpoints_map

    for endpoint_property in endpoints.additionalProperties:
      key, value = endpoint_property.key, endpoint_property.value
      endpoints_map[key] = value

    return endpoints_map

  def _build_interconnect_messages(self, interconnects_map):
    """Builds a WireGroupEndpoint.InterconnectsValue message.

    Args:
      interconnects_map: map of interconnects with label as the key and the
        interconnect message as the value

    Returns:
      WireGroupEndpoint.InterconnectsValue message
    """
    if not interconnects_map:
      return None

    interconnect_properties_list = []

    for (interconnect_label, interconnect_message) in interconnects_map.items():
      interconnect_properties_list.append(
          self._messages.WireGroupEndpoint.InterconnectsValue.AdditionalProperty(
              key=interconnect_label,
              value=interconnect_message,
          )
      )

    return self._messages.WireGroupEndpoint.InterconnectsValue(
        additionalProperties=interconnect_properties_list
    )

  def _build_endpoint_messages(self, endpoints_map):
    """Builds a WireGroup.EndpointValue message.

    This is so we can re-assign them to the additionalProperties attribute on
    the WireGroup.EndpointsValue message.

    Args:
      endpoints_map: map of endpoints with label as the key and the
        endpoint message as the value

    Returns:
      WireGroup.EndpointsValue message
    """
    if not endpoints_map:
      return None

    endpoint_properties_list = []

    for (endpoint_label, endpoints_message) in endpoints_map.items():
      endpoint_properties_list.append(
          self._messages.WireGroup.EndpointsValue.AdditionalProperty(
              key=endpoint_label,
              value=endpoints_message,
          )
      )

    return self._messages.WireGroup.EndpointsValue(
        additionalProperties=endpoint_properties_list
    )

RemoveInterconnect.detailed_help = DETAILED_HELP
