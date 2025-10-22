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

"""Command to create an HA Controller."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.ha_controllers import utils as api_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.ha_controllers import utils
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.compute.alpha import compute_alpha_messages


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create an HA Controller.

  Create an High Availability (HA) Controller, which helps
  ensure that a virtual machine (VM) instance remains operational by
  automatically managing failover across two zones.
  """

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    utils.AddHaControllerNameArgToParser(
        parser, base.ReleaseTrack.ALPHA.name.lower()
    )
    parser.add_argument(
        '--description',
        help=(
            'An optional, user-provided description for the HA Controller to'
            ' help identify its purpose.'
        ),
    )
    parser.add_argument(
        '--instance-name',
        help=(
            'The name of the existing VM that the HA Controller manages. This'
            ' VM must already exist in one of the zones specified in'
            ' --zone-configuration.'
        ),
    )
    parser.add_argument(
        '--failover-initiation',
        required=True,
        type=lambda x: arg_utils.ChoiceToEnum(
            x,
            compute_alpha_messages.HaController.FailoverInitiationValueValuesEnum,
        ),
        help=(
            'Specifies how a failover is triggered. Set to MANUAL_ONLY if you'
            ' want to trigger failovers yourself. Must be one of:'
            f' {utils.EnumTypeToChoices(compute_alpha_messages.HaController.FailoverInitiationValueValuesEnum)}'
        ),
    )
    parser.add_argument(
        '--secondary-zone-capacity',
        required=True,
        type=lambda x: arg_utils.ChoiceToEnum(
            x,
            compute_alpha_messages.HaController.SecondaryZoneCapacityValueValuesEnum,
        ),
        help=(
            'Determines the capacity guarantee in the secondary zone. Use'
            ' BEST_EFFORT to create a VM based on capacity availability at the'
            ' time of failover, suitable for workloads that can tolerate longer'
            ' recovery times. Must be one of:'
            f' {utils.EnumTypeToChoices(compute_alpha_messages.HaController.SecondaryZoneCapacityValueValuesEnum)}'
        ),
    )
    parser.add_argument(
        '--zone-configuration',
        required=True,
        type=arg_parsers.ArgObject(
            spec={
                'node-affinity': arg_parsers.ArgObject(
                    value_type=lambda x: arg_utils.ChoiceToEnum(
                        x,
                        compute_alpha_messages.HaControllerZoneConfigurationNodeAffinity.OperatorValueValuesEnum,
                    ),
                    help_text=(
                        'Specifies the node-affinity value.'
                        ' Must be one of:'
                        f' {utils.EnumTypeToChoices(compute_alpha_messages.HaControllerZoneConfigurationNodeAffinity.OperatorValueValuesEnum)}'
                    ),
                ),
                'reservation': arg_parsers.ArgObject(
                    value_type=str,
                    help_text=(
                        'Specifies the reservation name. The reservation must'
                        ' exist within the HA Controller region.'
                    ),
                ),
                'reservation-affinity': arg_parsers.ArgObject(
                    value_type=lambda x: arg_utils.ChoiceToEnum(
                        x,
                        compute_alpha_messages.HaControllerZoneConfigurationReservationAffinity.ConsumeReservationTypeValueValuesEnum,
                    ),
                    help_text=(
                        'Specifies the reservation-affinity value.'
                        ' Must be one of:'
                        f' {utils.EnumTypeToChoices(compute_alpha_messages.HaControllerZoneConfigurationReservationAffinity.ConsumeReservationTypeValueValuesEnum)}'
                    ),
                ),
                'zone': arg_parsers.ArgObject(
                    value_type=str,
                    help_text=(
                        'Specifies the zone. The zone must be within the HA'
                        ' Controller region.'
                    ),
                ),
            },
        ),
        action=arg_parsers.FlattenAction(),
        help=(
            'Configures the two zones for the HA Controller and specifies how'
            ' VM capacity is reserved in each zone. You must provide two zone'
            ' configurations. You can also specify an existing reservation or'
            ' node-group to guarantee capacity.'
        ),
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    ha_controller_ref = args.CONCEPTS.ha_controller.Parse()
    ha_controller = client.messages.HaController(
        name=ha_controller_ref.Name(),
        region=ha_controller_ref.region,
        description=args.description,
        instanceName=args.instance_name,
        failoverInitiation=args.failover_initiation,
        secondaryZoneCapacity=args.secondary_zone_capacity,
        zoneConfigurations=utils.MakeZoneConfiguration(args.zone_configuration),
    )
    if not args.async_:
      return api_utils.Insert(ha_controller, ha_controller_ref, holder)

    errors_to_collect = []
    response = api_utils.InsertAsync(
        client, ha_controller, ha_controller_ref, errors_to_collect
    )
    err = getattr(response, 'error', None)
    if err:
      errors_to_collect.append(poller.OperationErrors(err.errors))
    if errors_to_collect:
      raise core_exceptions.MultiError(errors_to_collect)

    operation_ref = holder.resources.Parse(response.selfLink)

    log.status.Print(
        'HA Controller creation in progress for [{}]: {}'.format(
            ha_controller.name, operation_ref.SelfLink()
        )
    )
    log.status.Print(
        'Use [gcloud compute operations describe URI] command '
        'to check the status of the operation.'
    )

    return response
