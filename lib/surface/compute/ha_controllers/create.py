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

"""Command to create an HA controller."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.ha_controllers import utils as api_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.ha_controllers import utils
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.compute.alpha import compute_alpha_messages

@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create an HA controller."""

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    utils.AddHaControllerNameArgToParser(
        parser, base.ReleaseTrack.ALPHA.name.lower()
    )
    parser.add_argument(
        '--description',
        help='Description of the HA controller.',
    )
    parser.add_argument(
        '--instance-name',
        help='Name of the instance that HaController is in charge of.',
    )
    parser.add_argument(
        '--failover-initiation',
        required=True,
        type=compute_alpha_messages.HaController.FailoverInitiationValueValuesEnum,
        help='Indicates how failover should be initiated.',
    )
    parser.add_argument(
        '--secondary-zone-capacity',
        required=True,
        type=compute_alpha_messages.HaController.SecondaryZoneCapacityValueValuesEnum,
        help='Indicates capacity guarantees in the secondary zone.',
    )
    parser.add_argument(
        '--zone-configuration',
        required=True,
        type=arg_parsers.ArgObject(
            spec={
                'zone': str,
                'reservation-affinity': (
                    compute_alpha_messages.HaControllerZoneConfigurationReservationAffinity.ConsumeReservationTypeValueValuesEnum
                ),
                'reservation': str,
                'node-affinity': (
                    compute_alpha_messages.HaControllerZoneConfigurationNodeAffinity.OperatorValueValuesEnum
                ),
            }
        ),
        action=arg_parsers.FlattenAction(),
        help='Zone configuration for HA controller.',
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
      return api_utils.Insert(client, ha_controller, ha_controller_ref)

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
        'HA controller creation in progress for [{}]: {}'.format(
            ha_controller.name, operation_ref.SelfLink()
        )
    )
    log.status.Print(
        'Use [gcloud compute operations describe URI] command '
        'to check the status of the operation.'
    )

    return response
