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
"""Command for setting machine resources for virtual machine instances."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instances import flags

_DETAILED_HELP = {
    "brief": (
        "Set machine resources for a Compute Engine virtual machine instance."
    ),
    "DESCRIPTION": (
        "Set machine resources, such as changing the number and/or type of "
        "accelerators, for a virtual machine instance."
    ),
    "EXAMPLES": (
        """\
        To change the number of accelerators and/or type of accelerators
        for an instance 'my-instance' in zone 'us-central1-a', run:

          $ {command} my-instance \\
            --zone=us-central1-a \\
            --accelerator-type=nvidia-h100-8gb \\
            --accelerator-count=2
        """
    ),
}


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA,
    base.ReleaseTrack.PREVIEW,
)
class SetMachineResources(base.SilentCommand):
  """Set machine resources for a Compute Engine virtual machine instance."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)
    accelerator_group = parser.add_argument_group()
    accelerator_group.add_argument(
        "--accelerator-type",
        required=True,
        help="The type of accelerator to attach to the instance.",
    )
    accelerator_group.add_argument(
        "--accelerator-count",
        required=True,
        type=int,
        help="The number of accelerators to attach to the instance.",
    )

  def Run(self, args):
    errors = []
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )
    accelerator_type_ref = holder.resources.Parse(
        args.accelerator_type,
        collection="compute.acceleratorTypes",
        params={
            "project": instance_ref.project,
            "zone": instance_ref.zone,
        },
    )

    accelerator_config = messages.AcceleratorConfig(
        acceleratorType=accelerator_type_ref.SelfLink(),
        acceleratorCount=args.accelerator_count,
    )

    request_field = messages.InstancesSetMachineResourcesRequest(
        guestAccelerators=[accelerator_config]
    )
    request = (
        client.apitools_client.instances,
        "SetMachineResources",
        messages.ComputeInstancesSetMachineResourcesRequest(
            project=instance_ref.project,
            zone=instance_ref.zone,
            instance=instance_ref.instance,
            instancesSetMachineResourcesRequest=request_field,
        ),
    )

    response = client.MakeRequests(requests=[request], errors_to_collect=errors)
    if errors:
      utils.RaiseToolException(
          errors, error_message="Could not set machine resources for instance."
      )

    return response[0]
