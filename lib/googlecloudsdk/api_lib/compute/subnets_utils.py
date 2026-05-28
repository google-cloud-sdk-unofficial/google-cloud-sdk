# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple subnets subcommands."""


from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.networks.subnets import flags
import six


def _CreateSecondaryRange(
    client,
    name,
    ip_cidr_range=None,
    reserved_internal_range=None,
    ip_version=None,
    ip_collection=None,
):
  """Creates a subnetwork secondary range."""
  secondary_range = client.messages.SubnetworkSecondaryRange(rangeName=name)
  if ip_cidr_range:
    secondary_range.ipCidrRange = ip_cidr_range
  if reserved_internal_range:
    secondary_range.reservedInternalRange = reserved_internal_range
  if ip_version:
    if isinstance(ip_version, six.string_types):
      secondary_range.ipVersion = (
          client.messages.SubnetworkSecondaryRange.IpVersionValueValuesEnum(
              ip_version))
    else:
      secondary_range.ipVersion = ip_version
  if ip_collection:
    secondary_range.ipCollection = ip_collection
  return secondary_range


def CreateSecondaryRanges(
    client,
    secondary_range,
    secondary_range_with_reserved_internal_range,
    secondary_ipv6_ranges,
):
  """Creates all secondary ranges of a subnet."""
  secondary_ranges = []
  range_names = set()
  range_configs = {}  # rangeName -> config dict

  if secondary_range:
    for r in secondary_range:
      for name, cidr in six.iteritems(r):
        range_names.add(name)
        range_configs[name] = {'ip_cidr_range': cidr}

  if secondary_range_with_reserved_internal_range:
    for r in secondary_range_with_reserved_internal_range:
      for name, internal_range in six.iteritems(r):
        range_names.add(name)
        if name not in range_configs:
          range_configs[name] = {}
        range_configs[name]['reserved_internal_range'] = internal_range

  if secondary_ipv6_ranges:
    for r in secondary_ipv6_ranges:
      if 'ipCidrRange' in r:
        raise calliope_exceptions.InvalidArgumentException(
            'ipCidrRange',
            'The [ipCidrRange] key is not supported for IPv6 secondary '
            'ranges. Please use [ipv6CidrRange] instead.',
        )
      name = r.get('rangeName')
      if name:
        range_names.add(name)
        range_configs[name] = {
            'ip_version': 'IPV6',
            'ip_cidr_range': r.get('ipv6CidrRange'),
            'ip_collection': r.get('ipCollection'),
        }

  for name in sorted(range_names):
    config = range_configs[name]
    secondary_ranges.append(
        _CreateSecondaryRange(
            client,
            name,
            ip_cidr_range=config.get('ip_cidr_range'),
            reserved_internal_range=config.get('reserved_internal_range'),
            ip_version=config.get('ip_version'),
            ip_collection=config.get('ip_collection'),
        )
    )
  return secondary_ranges


def MakeSubnetworkUpdateRequest(
    client,
    subnet_ref,
    enable_private_ip_google_access=None,
    allow_cidr_routes_overlap=None,
    add_secondary_ranges=None,
    add_secondary_ranges_with_reserved_internal_range=None,
    add_secondary_ipv6_ranges=None,
    remove_secondary_ranges=None,
    remove_secondary_ipv6_ranges=None,
    enable_flow_logs=None,
    aggregation_interval=None,
    flow_sampling=None,
    metadata=None,
    filter_expr=None,
    metadata_fields=None,
    set_new_purpose=None,
    set_role_active=None,
    drain_timeout_seconds=None,
    private_ipv6_google_access_type=None,
    stack_type=None,
    ipv6_access_type=None,
    external_ipv6_prefix=None,
    internal_ipv6_prefix=None,
    ip_collection=None,
    ipv6_network_tier=None,
):
  """Make the appropriate update request for the args.

  Args:
    client: GCE API client
    subnet_ref: Reference to a subnetwork
    enable_private_ip_google_access: Enable/disable access to Google Cloud APIs
      from this subnet for instances without a public ip address.
    allow_cidr_routes_overlap: Allow/Disallow this subnetwork's ranges to
      conflict with existing static routes.
    add_secondary_ranges: List of secondary IP ranges to add to the subnetwork
      for use in IP aliasing.
    add_secondary_ranges_with_reserved_internal_range: List of secondary IP
      ranges that are associated with InternalRange resources.
    add_secondary_ipv6_ranges: List of secondary IPv6 ranges to add to the
      subnetwork.
    remove_secondary_ranges: List of secondary ranges to remove from the
      subnetwork.
    remove_secondary_ipv6_ranges: List of secondary IPv6 ranges to remove from
      the subnetwork.
    enable_flow_logs: Enable/disable flow logging for this subnet.
    aggregation_interval: The internal at which to aggregate flow logs.
    flow_sampling: The sampling rate for flow logging in this subnet.
    metadata: Whether metadata fields should be added reported flow logs.
    filter_expr: custom CEL expression for filtering flow logs
    metadata_fields: custom metadata fields to be added to flow logs
    set_new_purpose: Update the purpose of the subnet.
    set_role_active: Updates the role of a BACKUP subnet to ACTIVE.
    drain_timeout_seconds: The maximum amount of time to drain connections from
      the active subnet to the backup subnet with set_role_active=True.
    private_ipv6_google_access_type: The private IPv6 google access type for the
      VMs in this subnet.
    stack_type: The stack type for this subnet.
    ipv6_access_type: The IPv6 access type for this subnet.
    external_ipv6_prefix: The IPv6 external prefix to be assigned to this
      subnet.
    internal_ipv6_prefix: The IPv6 internal prefix to be assigned to this
      subnet. When ULA is enabled, the prefix will be ignored.
    ip_collection: The IP collection that provisions BYOIP v6 addresses for this
      subnet.
    ipv6_network_tier: The IPv6 network tier for this subnet.

  Returns:
    response, result of sending the update request for the subnetwork
  """
  convert_to_enum = lambda x: x.replace('-', '_').upper()
  if enable_private_ip_google_access is not None:
    google_access = (
        client.messages.SubnetworksSetPrivateIpGoogleAccessRequest())
    google_access.privateIpGoogleAccess = enable_private_ip_google_access

    google_access_request = (
        client.messages.ComputeSubnetworksSetPrivateIpGoogleAccessRequest(
            project=subnet_ref.project,
            region=subnet_ref.region,
            subnetwork=subnet_ref.Name(),
            subnetworksSetPrivateIpGoogleAccessRequest=google_access))
    return client.MakeRequests([
        (client.apitools_client.subnetworks, 'SetPrivateIpGoogleAccess',
         google_access_request)
    ])
  elif (
      add_secondary_ranges is not None
      or add_secondary_ipv6_ranges is not None
      or add_secondary_ranges_with_reserved_internal_range is not None
  ):
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.secondaryIpRanges = original_subnetwork.secondaryIpRanges
    subnetwork.fingerprint = original_subnetwork.fingerprint

    subnetwork.secondaryIpRanges.extend(
        CreateSecondaryRanges(
            client,
            add_secondary_ranges,
            add_secondary_ranges_with_reserved_internal_range,
            add_secondary_ipv6_ranges,
        )
    )

    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)])
  elif (
      remove_secondary_ranges is not None
      or remove_secondary_ipv6_ranges is not None
  ):
    ranges_to_remove = []
    if remove_secondary_ranges:
      # Because flags.py uses action='append' combined with
      # type=arg_parsers.ArgsList, remove_secondary_ranges is a
      # list of lists.
      # ex. --remove-secondary-ranges r1,r2 --remove-secondary-ranges r3 results
      # in [['r1', 'r2'], ['r3']], but current implementation will only iterate
      # through the first list.
      ranges_to_remove.extend(remove_secondary_ranges[0])
    if remove_secondary_ipv6_ranges:
      # For secondary ipv6 ranges, flags.py does not use action='append' hence
      # argument is a simple list ex. ['r1', 'r2'].
      ranges_to_remove.extend(remove_secondary_ipv6_ranges)
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.secondaryIpRanges = original_subnetwork.secondaryIpRanges
    subnetwork.fingerprint = original_subnetwork.fingerprint

    for name in ranges_to_remove:
      if name not in [r.rangeName for r in subnetwork.secondaryIpRanges]:
        raise calliope_exceptions.UnknownArgumentException(
            'remove-secondary-ranges', 'Subnetwork does not have a range {}, '
            'present ranges are {}.'.format(
                name, [r.rangeName for r in subnetwork.secondaryIpRanges]))
    subnetwork.secondaryIpRanges = [
        r
        for r in original_subnetwork.secondaryIpRanges
        if r.rangeName not in ranges_to_remove
    ]

    cleared_fields = []
    if not subnetwork.secondaryIpRanges:
      cleared_fields.append('secondaryIpRanges')
    with client.apitools_client.IncludeFields(cleared_fields):
      return client.MakeRequests(
          [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)])
  elif (enable_flow_logs is not None or aggregation_interval is not None or
        flow_sampling is not None or metadata is not None or
        filter_expr is not None or metadata_fields is not None):
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint

    log_config = client.messages.SubnetworkLogConfig(enable=enable_flow_logs)
    if aggregation_interval is not None:
      log_config.aggregationInterval = flags.GetLoggingAggregationIntervalArg(
          client.messages).GetEnumForChoice(aggregation_interval)
    if flow_sampling is not None:
      log_config.flowSampling = flow_sampling
    if metadata is not None:
      log_config.metadata = flags.GetLoggingMetadataArg(
          client.messages).GetEnumForChoice(metadata)
    if filter_expr is not None:
      log_config.filterExpr = filter_expr
    if metadata_fields is not None:
      log_config.metadataFields = metadata_fields
    subnetwork.logConfig = log_config

    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)])
  elif private_ipv6_google_access_type is not None:
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint

    subnetwork.privateIpv6GoogleAccess = (
        client.messages.Subnetwork.PrivateIpv6GoogleAccessValueValuesEnum(
            ConvertPrivateIpv6GoogleAccess(
                convert_to_enum(private_ipv6_google_access_type))))
    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)])
  elif allow_cidr_routes_overlap is not None:
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([(
        client.apitools_client.subnetworks,
        'Get',
        client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()),
    )])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint

    subnetwork.allowSubnetCidrRoutesOverlap = allow_cidr_routes_overlap
    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)]
    )
  elif set_new_purpose is not None:
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint

    subnetwork.purpose = client.messages.Subnetwork.PurposeValueValuesEnum(
        set_new_purpose)
    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)])
  elif set_role_active is not None:
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([
        (client.apitools_client.subnetworks, 'Get',
         client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()))
    ])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint

    subnetwork.role = client.messages.Subnetwork.RoleValueValuesEnum.ACTIVE
    patch_request = client.messages.ComputeSubnetworksPatchRequest(
        project=subnet_ref.project,
        subnetwork=subnet_ref.subnetwork,
        region=subnet_ref.region,
        subnetworkResource=subnetwork,
        drainTimeoutSeconds=drain_timeout_seconds,
    )
    return client.MakeRequests(
        [(client.apitools_client.subnetworks, 'Patch', patch_request)]
    )
  elif (
      stack_type is not None
      or ip_collection is not None
      or ipv6_access_type is not None
      or external_ipv6_prefix is not None
      or internal_ipv6_prefix is not None
      or ipv6_network_tier is not None
  ):
    subnetwork = client.messages.Subnetwork()
    original_subnetwork = client.MakeRequests([(
        client.apitools_client.subnetworks,
        'Get',
        client.messages.ComputeSubnetworksGetRequest(**subnet_ref.AsDict()),
    )])[0]
    subnetwork.fingerprint = original_subnetwork.fingerprint
    if stack_type is not None:
      subnetwork.stackType = (
          client.messages.Subnetwork.StackTypeValueValuesEnum(stack_type)
      )
    if ipv6_access_type is not None:
      subnetwork.ipv6AccessType = (
          client.messages.Subnetwork.Ipv6AccessTypeValueValuesEnum(
              ipv6_access_type
          )
      )
    if external_ipv6_prefix is not None:
      subnetwork.externalIpv6Prefix = external_ipv6_prefix
    if internal_ipv6_prefix is not None:
      subnetwork.internalIpv6Prefix = internal_ipv6_prefix
    if ip_collection is not None:
      subnetwork.ipCollection = ip_collection
    if ipv6_network_tier is not None:
      subnetwork.ipv6NetworkTier = (
          client.messages.Subnetwork.Ipv6NetworkTierValueValuesEnum(
              ipv6_network_tier
          )
      )
    return client.MakeRequests(
        [CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork)]
    )

  return client.MakeRequests([])


def CreateSubnetworkPatchRequest(client, subnet_ref, subnetwork_resource):
  patch_request = client.messages.ComputeSubnetworksPatchRequest(
      project=subnet_ref.project,
      subnetwork=subnet_ref.subnetwork,
      region=subnet_ref.region,
      subnetworkResource=subnetwork_resource)
  return (client.apitools_client.subnetworks, 'Patch', patch_request)


def ConvertPrivateIpv6GoogleAccess(choice):
  """Return PrivateIpv6GoogleAccess enum defined in mixer.

  Args:
    choice: Enum value of PrivateIpv6GoogleAccess defined in gcloud.
  """
  choices_to_enum = {
      'DISABLE': 'DISABLE_GOOGLE_ACCESS',
      'ENABLE_BIDIRECTIONAL_ACCESS': 'ENABLE_BIDIRECTIONAL_ACCESS_TO_GOOGLE',
      'ENABLE_OUTBOUND_VM_ACCESS': 'ENABLE_OUTBOUND_VM_ACCESS_TO_GOOGLE',
  }
  return choices_to_enum.get(choice)
