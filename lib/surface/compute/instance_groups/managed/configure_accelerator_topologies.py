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

"""Command for configuring accelerator topologies of a MIG."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import (
    flags as instance_groups_flags,
)

DETAILED_HELP = {
    'brief': (
        'Configure accelerator topologies of a Compute Engine '
        'managed instance group.'
    ),
    'DESCRIPTION': (
        """
        *{command}* configures the state of accelerator topologies for a Compute
        Engine managed instance group (MIG).

        Accelerator topologies represent physical or logical groupings of
        tightly coupled hardware resources, such as TPU slices or advanced GPU
        clusters, connected via high-speed interconnects.

        You can use this command to activate or deactivate specific accelerator
        topologies, or to assign external identifiers to them. To discover the
        available accelerator topology IDs for your managed instance group, use
        the `getAvailableAcceleratorTopologies` API method.
    """
    ),
    'EXAMPLES': (
        """
        To activate an accelerator topology with ID `topology-1` for a managed
        instance group named `my-mig` in zone `us-central1-a`, run:

          $ {command} my-mig --zone=us-central1-a \\
              --accelerator-topology-actions=topology-1=ACTIVATE

        To deactivate an accelerator topology `topology-1` and simultaneously
        activate `topology-2`, run:

          $ {command} my-mig --zone=us-central1-a \\
              --accelerator-topology-actions=topology-1=DEACTIVATE,\\
              topology-2=ACTIVATE

        To configure an accelerator topology `topology-1` with an external
        identifier `ext-slice-123` and set its action to `ACTIVATE`, run:

          $ {command} my-mig --zone=us-central1-a \\
              --accelerator-topology-configurations=topology=topology-1,\\
              action=ACTIVATE,external-id=ext-slice-123
    """
    ),
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class ConfigureAcceleratorTopologies(base.Command):
  """Configure accelerator topologies of a managed instance group."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.MakeZonalInstanceGroupManagerArg().AddArgument(parser)
    mutex_group = parser.add_group(mutex=True)
    mutex_group.add_argument(
        '--accelerator-topology-actions',
        type=arg_parsers.ArgDict(),
        metavar='TOPOLOGY_ID=ACTION',
        help=(
            'A map of accelerator topologies that should have their state '
            'changed to the specified action. The key is the accelerator '
            'topology ID (obtained from `getAvailableAcceleratorTopologies`), '
            'and the value is the desired action (`ACTIVATE` or `DEACTIVATE`).'
        ),
    )
    mutex_group.add_argument(
        '--accelerator-topology-configurations',
        type=arg_parsers.ArgDict(
            spec={
                'topology': str,
                'action': str,
                'external-id': str,
            }
        ),
        metavar=(
            'topology=TOPOLOGY_ID,[action=ACTION],[external-id=EXTERNAL_ID]'
        ),
        help=(
            'A map of accelerator topologies that should have their '
            'configuration changed. Subkeys must include `topology` (the '
            'accelerator topology ID obtained from '
            '`getAvailableAcceleratorTopologies`), and can include `action` '
            '(`ACTIVATE` or `DEACTIVATE`) and `external-id` (an external '
            'identifier used to uniquely identify the topology).'
        ),
    )

  def _GetAcceleratorTopologyActions(self, args, actions_val_cls):
    """Parses accelerator topology actions from command arguments."""
    if not args.accelerator_topology_actions:
      return None
    additional_props = []
    for topology_id, action_str in sorted(
        args.accelerator_topology_actions.items()
    ):
      action_enum = getattr(
          actions_val_cls.AdditionalProperty.ValueValueValuesEnum,
          action_str,
      )
      additional_props.append(
          actions_val_cls.AdditionalProperty(
              key=topology_id, value=action_enum
          )
      )
    return actions_val_cls(additionalProperties=additional_props)

  def _GetAcceleratorTopologyConfigurations(
      self, args, configs_val_cls, config_cls
  ):
    """Parses accelerator topology configurations from command arguments."""
    if not args.accelerator_topology_configurations:
      return None
    config_dict = args.accelerator_topology_configurations
    topology_id = config_dict.get('topology')
    if not topology_id:
      raise exceptions.RequiredArgumentException(
          '--accelerator-topology-configurations',
          'The [topology] key is required in '
          '--accelerator-topology-configurations.',
      )
    config_msg = config_cls()
    if 'action' in config_dict:
      config_msg.action = getattr(
          config_cls.ActionValueValuesEnum,
          config_dict['action'],
      )
    if 'external-id' in config_dict:
      config_msg.externalId = config_dict['external-id']

    return configs_val_cls(
        additionalProperties=[
            configs_val_cls.AdditionalProperty(
                key=topology_id, value=config_msg
            )
        ]
    )

  def Run(self, args):
    if (
        not args.accelerator_topology_actions
        and not args.accelerator_topology_configurations
    ):
      raise exceptions.OneOfArgumentsRequiredException(
          [
              '--accelerator-topology-actions',
              '--accelerator-topology-configurations',
          ],
          'At least one map of accelerator topology modifications must be '
          'specified.',
      )

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    req_cls = (
        messages.InstanceGroupManagersConfigureAcceleratorTopologiesRequest
    )
    config_cls = getattr(
        messages,
        'InstanceGroupManagersConfigureAcceleratorTopologiesRequest'
        'AcceleratorTopologyConfiguration',
    )
    outer_req_cls = getattr(
        messages,
        'ComputeInstanceGroupManagersConfigureAcceleratorTopologiesRequest',
    )

    resource_arg = instance_groups_flags.MakeZonalInstanceGroupManagerArg()
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.ZONE,
        scope_lister=flags.GetDefaultScopeLister(client),
    )

    actions_val = self._GetAcceleratorTopologyActions(
        args, req_cls.AcceleratorTopologyActionsValue
    )
    configs_val = self._GetAcceleratorTopologyConfigurations(
        args, req_cls.AcceleratorTopologyConfigurationsValue, config_cls
    )

    inner_request = req_cls(
        acceleratorTopologyActions=actions_val,
        acceleratorTopologyConfigurations=configs_val,
    )

    request = outer_req_cls(
        instanceGroupManager=igm_ref.Name(),
        instanceGroupManagersConfigureAcceleratorTopologiesRequest=inner_request,
        project=igm_ref.project,
        zone=igm_ref.zone,
    )

    return client.MakeRequests([(
        client.apitools_client.instanceGroupManagers,
        'ConfigureAcceleratorTopologies',
        request,
    )])

