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
"""Command for listing referrers of an instance."""


from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags

_DETAILED_HELP = {
    'brief': 'List referrers to a Compute Engine virtual machine instance.',
    'DESCRIPTION': (
        """\
        Retrieves a list of resources that refer to the VM instance specified
        in the request. For example, if the VM instance is part of a managed or
        unmanaged instance group, the referrers list includes the instance
        group.
        """
    ),
    'EXAMPLES': (
        """\
        To list referrers to an instance named `my-instance` in zone
        `us-central1-a`, run:

          $ {command} my-instance --zone=us-central1-a
        """
    ),
}

_DISPLAY_INFO_FORMAT = """\
      table(
        referrer:label=REFERRER,
        referenceType:label=REFERENCE_TYPE,
        target:label=TARGET
      )"""


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA,
    base.ReleaseTrack.PREVIEW,
)
class ListReferrers(base.ListCommand):
  """List referrers to a Compute Engine virtual machine instance."""

  detailed_help = _DETAILED_HELP
  display_info_format = _DISPLAY_INFO_FORMAT

  @classmethod
  def Args(cls, parser):
    base.URI_FLAG.RemoveFromParser(parser)
    flags.INSTANCE_ARG.AddArgument(
        parser, operation_type='list referrers for'
    )
    parser.display_info.AddFormat(cls.display_info_format)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client),
    )

    request = messages.ComputeInstancesListReferrersRequest(
        instance=instance_ref.instance,
        zone=instance_ref.zone,
        project=instance_ref.project,
    )

    return list_pager.YieldFromList(
        service=client.apitools_client.instances,
        request=request,
        method='ListReferrers',
        field='items',
        limit=args.limit,
        batch_size=args.page_size,
    )
