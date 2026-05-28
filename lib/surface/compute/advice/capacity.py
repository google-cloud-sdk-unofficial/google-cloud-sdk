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
"""Command to get capacity advice for Compute Engine resources."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute.advice import flags
from googlecloudsdk.core import properties


DETAILED_HELP = {
    "DESCRIPTION": """
      Get capacity advice for Compute Engine resources.

      This command helps you view future resource availability for a specific
      number of VM instances, machine type, provisioning model, and zone. After
      you confirm resource availability, you can specify those configurations
      when you create VM instances. This action improves the success rate of
      your VM instance creation request.
    """,
    "EXAMPLES": """
      To check the availability of 100 `n2-standard-32` Spot VMs in any single
      zone in the `us-central1` region, run the following command:

        $ {command} \
            --region="us-central1" \
            --provisioning-model="SPOT" \
            --size=100 \
            --instance-selection-machine-types="n2-standard-32" \
            --target-distribution-shape="any-single-zone"

      To check the availability of 50 Spot VMs, allowing either `e2-standard-8`
      or `e2-standard-16` machine types, distributed across `us-central1-a` and
      `us-central1-b`, run the following command:

        $ {command} \
            --region="us-central1" \
            --provisioning-model="SPOT" \
            --size=50 \
            --instance-selection="name=my-selection,machine-type=e2-standard-8,machine-type=e2-standard-16" \
            --target-distribution-shape="any" \
            --zones="us-central1-a,us-central1-b"

      To check the availability of 10 `ct5lp-hightpu-4t` Flex-start VMs that
      will run for 1 day in any single zone in the `us-central1` region, run the
      following command:

        $ {command} \
            --region="us-central1" \
            --provisioning-model="FLEX_START" \
            --max-run-duration=1d \
            --size=10 \
            --instance-selection-machine-types="ct5lp-hightpu-4t" \
            --target-distribution-shape="any-single-zone" \
            --accelerator-topology="2x2"
      """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Capacity(base.Command):
  """Get capacity advice for Compute Engine resources."""

  detailed_help = DETAILED_HELP
  category = base.COMPUTE_CATEGORY

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    flags.AddRegionFlag(parser)
    flags.AddProvisioningModelFlag(parser)
    flags.AddMaxRunDurationFlag(parser)
    flags.AddAcceleratorTopologyFlag(parser)
    parser.add_argument(
        "--size",
        type=int,
        required=True,
        help="The total number of VMs being requested in the capacity query.",
    )

    flags.AddInstanceFlexibilityPolicyArgs(parser)

    flags.AddTargetDistributionShapeFlag(parser)
    parser.add_argument(
        "--zones",
        type=arg_parsers.ArgList(),
        completer=completers.ZonesCompleter,
        metavar="ZONE",
        required=False,
        help=(
            "A comma-separated list of zones to query within the specified"
            " region, for example, `us-central1-a,us-central1-b`. If you omit"
            " this flag, then you view availability for your requested capacity"
            " across all zones in the region."
        ),
    )

  def Run(self, args):
    """Runs the capacity advice command."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages
    flags.ValidateZonesAndRegionFlags(args, holder.resources)

    if args.instance_selection and len(args.instance_selection) > 1:
      raise exceptions.InvalidArgumentException(
          "--instance-selection",
          "Multiple instance selections are not supported. Please provide only"
          " one --instance-selection flag.",
      )
    if (
        args.instance_selection_machine_types
        and len(args.instance_selection_machine_types) > 1
    ):
      raise exceptions.InvalidArgumentException(
          "--instance-selection-machine-types",
          "Multiple instance selections are not supported. Please provide only"
          " one --instance-selection-machine-types flag.",
      )

    if args.instance_selection:
      for selection in args.instance_selection:
        if not selection.get("machine-type"):
          raise exceptions.InvalidArgumentException(
              "--instance-selection",
              "At least one 'machine-type' must be specified in each"
              " --instance-selection flag.",
          )

    project = properties.VALUES.core.project.GetOrFail()
    region = args.region
    if not region and args.zones:
      # All zones are in the same region, this is validated in
      # ValidateZonesAndRegionFlags.
      region = utils.ZoneNameToRegionName(args.zones[0])

    region = region or properties.VALUES.compute.region.Get()
    if not region:
      raise exceptions.RequiredArgumentException(
          "--region", "The [compute/region] property must be set.")

    # Instance Properties
    scheduling = messages.CapacityAdviceRequestInstancePropertiesScheduling(
        provisioningModel=messages.CapacityAdviceRequestInstancePropertiesScheduling.ProvisioningModelValueValuesEnum(
            args.provisioning_model
        )
    )

    if args.provisioning_model == "FLEX_START" and not args.IsSpecified(
        "max_run_duration"
    ):
      raise exceptions.RequiredArgumentException(
          "--max_run_duration",
          "The --max-run-duration flag is required when the provisioning model"
          " is FLEX_START.",
      )

    if args.IsSpecified("max_run_duration"):
      scheduling.maxRunDuration = f"{args.max_run_duration}s"

    instance_properties = messages.CapacityAdviceRequestInstanceProperties(
        scheduling=scheduling)
    if args.IsSpecified("accelerator_topology"):
      instance_properties.acceleratorTopology = args.accelerator_topology

    # Distribution Policy
    target_shape = None
    if args.IsSpecified("target_distribution_shape"):
      target_shape = (
          messages.CapacityAdviceRequestDistributionPolicy.TargetShapeValueValuesEnum(
              args.target_distribution_shape)
      )
    zone_configs = None
    if args.zones:
      zone_configs = []
      for zone in args.zones:
        zone_ref = holder.resources.Parse(
            zone,
            params={"project": project},
            collection="compute.zones")
        zone_configs.append(
            messages.CapacityAdviceRequestDistributionPolicyZoneConfiguration(
                zone=zone_ref.SelfLink()))
    distribution_policy = messages.CapacityAdviceRequestDistributionPolicy(
        targetShape=target_shape)
    if zone_configs:
      distribution_policy.zones = zone_configs
    selections_map = {}
    if args.instance_flexibility_policy:
      raw_selections = args.instance_flexibility_policy.get(
          "instanceSelections",
          args.instance_flexibility_policy.get("instance-selections", {})
      )
      items = []
      if isinstance(raw_selections, dict):
        items = list(raw_selections.items())
      elif isinstance(raw_selections, list):
        for sel in raw_selections:
          if not isinstance(sel, dict):
            raise exceptions.InvalidArgumentException(
                "--instance-flexibility-policy",
                "Each instance selection must be a dictionary.",
            )
          if "name" not in sel:
            raise exceptions.InvalidArgumentException(
                "--instance-flexibility-policy",
                "Missing instance selection name."
            )
          items.append((sel["name"], sel))

      for name, selection_info in items:
        machine_types = selection_info.get(
            "machineTypes",
            selection_info.get("machine-types", [])
        )
        selection = messages.CapacityAdviceRequestInstanceFlexibilityPolicyInstanceSelection(
            machineTypes=machine_types,
        )
        if "rank" in selection_info:
          selection.rank = int(selection_info["rank"])
        min_cpu = selection_info.get("minCpuPlatform") or selection_info.get(
            "min-cpu-platform"
        )
        if min_cpu:
          selection.minCpuPlatform = min_cpu
        if "disks" in selection_info:
          disks = []
          for disk_dict in selection_info["disks"]:
            disks.append(
                encoding.DictToMessage(disk_dict, messages.AttachedDisk)
            )
          selection.disks = disks
        selections_map[name] = selection
    elif args.instance_selection:
      for i, selection in enumerate(args.instance_selection):
        selection_name_list = selection.get("name")
        selection_name = (
            selection_name_list[0]
            if selection_name_list
            else "instance-selection-{}".format(i + 1)
        )
        if selection_name in selections_map:
          raise exceptions.InvalidArgumentException(
              "--instance-selection",
              "Duplicate instance selection name [{}] specified.".format(
                  selection_name
              ),
          )
        inst_sel = messages.CapacityAdviceRequestInstanceFlexibilityPolicyInstanceSelection(
            machineTypes=selection.get("machine-type"),
        )
        if "rank" in selection:
          inst_sel.rank = int(selection["rank"][0])
        if "min-cpu-platform" in selection:
          min_cpu_platform = selection["min-cpu-platform"]
          if isinstance(min_cpu_platform, list):
            inst_sel.minCpuPlatform = min_cpu_platform[0]
          else:
            inst_sel.minCpuPlatform = min_cpu_platform
        selections_map[selection_name] = inst_sel
    elif args.instance_selection_machine_types:
      for i, machine_types_list in enumerate(
          args.instance_selection_machine_types
      ):
        selection_name = "instance-selection-{}".format(i + 1)
        selections_map[selection_name] = (
            messages.CapacityAdviceRequestInstanceFlexibilityPolicyInstanceSelection(
                machineTypes=machine_types_list,
            )
        )

    additional_properties = []
    for key, value in selections_map.items():
      additional_properties.append(
          messages.CapacityAdviceRequestInstanceFlexibilityPolicy.InstanceSelectionsValue.AdditionalProperty(
              key=key, value=value)
      )

    instance_selections_value = (
        messages.CapacityAdviceRequestInstanceFlexibilityPolicy.InstanceSelectionsValue(
            additionalProperties=additional_properties
        )
    )
    instance_flexibility_policy = (
        messages.CapacityAdviceRequestInstanceFlexibilityPolicy(
            instanceSelections=instance_selections_value
        )
    )

    inner_request = messages.CapacityAdviceRequest(
        distributionPolicy=distribution_policy,
        instanceFlexibilityPolicy=instance_flexibility_policy,
        instanceProperties=instance_properties,
        size=args.size,
    )

    outer_request = messages.ComputeAdviceCapacityRequest(
        project=project,
        region=region,
        capacityAdviceRequest=inner_request,
    )

    return client.apitools_client.advice.Capacity(outer_request)
