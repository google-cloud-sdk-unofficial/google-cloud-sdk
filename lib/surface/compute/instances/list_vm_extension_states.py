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
"""Command to list VM extension states for a Compute Engine instance."""


from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instances import flags

_DETAILED_HELP = {
    "brief": "List VM extension states.",
    "DESCRIPTION": (
        "List VM extension states for a Google Compute Engine instance."
    ),
    "EXAMPLES": (
        """\
        To list the VM extension states for an instance named
        `my-instance` in zone `us-central1-a` and in project `my-project`, run:

        $ {command} my-instance --zone=us-central1-a --project=my-project"""
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListVmExtensionStates(base.ListCommand):
  """List VM extension states for a Compute Engine instance."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(
        parser, operation_type="list VM extension states for"
    )
    parser.display_info.AddFormat("""
        table(
            name:label=EXTENSION_NAME,
            enforcementState:label=ENFORCEMENT_STATE,
            healthStatus:label=HEALTH_STATUS
        )
        """)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    request = client.messages.ComputeInstancesListVmExtensionStatesRequest(
        instance=instance_ref.instance,
        zone=instance_ref.zone,
        project=instance_ref.project,
    )

    return list_pager.YieldFromList(
        service=client.apitools_client.instances,
        request=request,
        method="ListVmExtensionStates",
        field="items",
        limit=args.limit,
        batch_size_attribute="maxResults",
        batch_size=args.page_size,
    )
