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
"""Command to show historical data on Spot VMs preemption and price."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import properties


DETAILED_HELP = {
    "DESCRIPTION": (
        """
      Show historical data on Spot VMs preemption and price.

      Use this command to retrieve historical data on Spot VM preemption and price for a specific machine type and location. By analyzing historical trends, you can choose configurations for creating new VM instances that increase stability or lower your costs.
    """
    ),
    "EXAMPLES": (
        """
      To check recent price history for `n2-standard-32` Spot VMs in `us-central1`, run the following command:

        $ {command} \
            --provisioning-model=SPOT \
            --machine-type=n2-standard-32 \
            --types=PRICE \
            --region=us-central1

      To check recent preemption and price history for `n2-standard-32` Spot VMs in `us-central1-a`, run the following command:

        $ {command} \
            --provisioning-model=SPOT \
            --machine-type=n2-standard-32 \
            --types=PREEMPTION,PRICE \
            --zone=us-central1-a
      """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CapacityHistory(base.Command):
  """Show historical data on Spot VMs preemption and price."""

  detailed_help = DETAILED_HELP
  category = base.COMPUTE_CATEGORY

  provisioning_model_choices = {
      "SPOT": (
          "Compute Engine may preempt a Spot VM whenever it needs capacity. "
          "Because Spot VMs don't have a guaranteed runtime, they come at a "
          "discounted price."
      ),
  }

  history_type_choices = {
      "PRICE": (
          "Historical Spot VMs prices in USD. For more information about Spot"
          " VMs pricing, see:"
          " https://docs.cloud.google.com/compute/docs/instances/spot#pricing "
      ),
      "PREEMPTION": (
          "Historical preemption rates for Spot VMs, calculated as the number"
          " of Spot VMs preempted by Compute Engine divided by the total number"
          " of Spot VMs suspended, stopped, or deleted by users, or stopped or"
          " deleted resulting from preemption. The rate is expressed in"
          " decimal numbers. For more information about the preemption process,"
          " see:"
          " https://docs.cloud.google.com/compute/docs/instances/spot#preemption"
      ),
  }

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    parser.add_argument(
        "--provisioning-model",
        choices=CapacityHistory.provisioning_model_choices,
        type=arg_utils.ChoiceToEnumName,
        required=True,
        help="Specifies the provisioning model.",
    )

    parser.add_argument(
        "--machine-type",
        type=str,
        required=True,
        help="The machine type for the VM, such as `n2-standard-4`.",
    )

    parser.add_argument(
        "--types",
        type=arg_parsers.ArgList(
            element_type=arg_utils.ChoiceToEnumName,
            min_length=1,
            choices=CapacityHistory.history_type_choices,
        ),
        metavar="HISTORY_TYPE",
        required=True,
        help="Specifies types of the request query.",
    )

    location_group = parser.add_group(
        required=True,
        mutex=True,
    )
    compute_flags.AddRegionFlag(
        parser=location_group,
        resource_type="advice",
        operation_type="get history",
    )
    location_group.add_argument(
        "--zone",
        type=str,
        help=(
            "The zone to query within the specified region, for example,"
            " `us-central1-a`. If omitted, you will view history"
            " across all zones in the region."
        ),
    )

  def Run(self, args):
    """Runs the command."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    project = properties.VALUES.core.project.GetOrFail()
    region = args.region or properties.VALUES.compute.region.Get()
    location_policy = None
    if args.zone:
      region = utils.ZoneNameToRegionName(args.zone)
      location_policy = messages.CapacityHistoryRequestLocationPolicy(
          location=f"zones/{args.zone}"
      )

    if not region:
      raise exceptions.OneOfArgumentsRequiredException(
          ["--region", "--zone"],
          "Either --region or --zone must be specified.",
      )

    scheduling = messages.CapacityHistoryRequestInstancePropertiesScheduling(
        provisioningModel=messages.CapacityHistoryRequestInstancePropertiesScheduling.ProvisioningModelValueValuesEnum(
            args.provisioning_model
        ),
    )

    instance_properties = messages.CapacityHistoryRequestInstanceProperties(
        scheduling=scheduling,
        machineType=args.machine_type,
    )

    inner_request = messages.CapacityHistoryRequest(
        instanceProperties=instance_properties,
        types=[
            messages.CapacityHistoryRequest.TypesValueListEntryValuesEnum(t)
            for t in args.types
        ],
        locationPolicy=location_policy,
    )

    outer_request = messages.ComputeAdviceCapacityHistoryRequest(
        project=project,
        region=region,
        capacityHistoryRequest=inner_request,
    )

    return client.apitools_client.advice.CapacityHistory(outer_request)
