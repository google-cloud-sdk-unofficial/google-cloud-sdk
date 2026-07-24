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
"""Command for adopting instances into a managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import path_simplifier
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class AdoptInstances(base.Command):
  """Adopt instances into a regional managed instance group."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
        table(project(),
              zone(),
              instanceName:label=INSTANCE,
              status)""")
    parser.add_argument(
        '--instances',
        type=arg_parsers.ArgList(min_length=1),
        metavar='INSTANCE',
        required=True,
        help='Names of instances to adopt.')
    instance_groups_flags.MakeRegionalInstanceGroupManagerArg().AddArgument(
        parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    resource_arg = instance_groups_flags.MakeRegionalInstanceGroupManagerArg()
    default_scope = compute_scope.ScopeEnum.REGION
    scope_lister = flags.GetDefaultScopeLister(client)
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=default_scope,
        scope_lister=scope_lister)

    instances_self_links = self._GetInstancesSelfLinks(
        client, igm_ref, args.instances
    )

    per_instance_configs = [
        client.messages.PerInstanceConfig(name=path_simplifier.Name(name))
        for name in args.instances
    ]
    request = (
        client.messages
        .ComputeRegionInstanceGroupManagersAdoptInstancesRequest(
            instanceGroupManager=igm_ref.Name(),
            regionInstanceGroupManagersAdoptInstancesRequest=(
                client.messages
                .RegionInstanceGroupManagersAdoptInstancesRequest(
                    instances=per_instance_configs
                )
            ),
            project=igm_ref.project,
            region=igm_ref.region,
        )
    )

    requests = instance_groups_utils.SplitInstancesInRequest(
        request, 'regionInstanceGroupManagersAdoptInstancesRequest')
    service = client.apitools_client.regionInstanceGroupManagers
    request_tuples = instance_groups_utils.GenerateRequestTuples(
        service, 'AdoptInstances', requests)

    errors = []
    client.MakeRequests(list(request_tuples), errors)

    if errors:
      utils.RaiseToolException(errors)

    status_per_instance = []
    for instance_name in args.instances:
      short_name = path_simplifier.Name(instance_name)
      status_per_instance.append({
          'selfLink': instances_self_links.get(short_name, instance_name),
          'instanceName': short_name,
          'status': 'SUCCESS',
      })
    return status_per_instance

  def _GetInstancesSelfLinks(self, client, igm_ref, instances):
    """Retrieves self links for instances.

    Args:
      client: The ComputeApiHolder client.
      igm_ref: The instance group manager reference.
      instances: A list of instance names or self links.

    Returns:
      A dict mapping instance names (as shortened by path_simplifier) to their
      self links.
    """
    instances_self_links = {}
    instances_to_resolve = []
    for name in instances:
      if '/zones/' in name:
        instances_self_links[path_simplifier.Name(name)] = name
      else:
        instances_to_resolve.append(name)

    if not instances_to_resolve:
      return instances_self_links

    filter_expr = ' OR '.join(
        ['name = "{0}"'.format(n) for n in instances_to_resolve])
    aggregated_request = (
        client.messages.ComputeInstancesAggregatedListRequest(
            project=igm_ref.project,
            filter=filter_expr,
            includeAllScopes=True,
        )
    )
    errors = []
    instances_found = client.MakeRequests(
        [(
            client.apitools_client.instances,
            'AggregatedList',
            aggregated_request,
        )],
        errors,
    )
    if errors:
      utils.RaiseToolException(errors)
    for instance in instances_found:
      if igm_ref.region in instance.selfLink:
        instances_self_links[instance.name] = instance.selfLink

    return instances_self_links


AdoptInstances.detailed_help = {
    'brief':
        'Adopt instances into a regional managed instance group.',
    'DESCRIPTION':
        """
        *{command}* adopts one or more existing unmanaged instances into a
regional managed instance group, thereby increasing the targetSize of the group.

Adopting an instance does not reboot or modify the underlying virtual machine
instances, but adds the instances to the instance group and applies any target
pools or backend services configured for the group.

Currently, adopting instances is only supported for regional managed
instance groups.
""",
}
