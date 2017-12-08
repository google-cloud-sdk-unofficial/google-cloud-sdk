# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Command for updating Google Compute Engine routers."""

import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.command_lib.compute.routers import router_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  """Update a Google Compute Engine router."""

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser)
    router_utils.AddCustomAdvertisementArgs(parser, 'router')

  def Run(self, args):
    # Manually ensure replace/incremental flags are mutually exclusive.
    router_utils.CheckIncompatibleFlagsOrRaise(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    service = holder.client.apitools_client.routers

    ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)

    request_type = messages.ComputeRoutersGetRequest
    existing = service.Get(request_type(**ref.AsDict()))
    replacement = copy.deepcopy(existing)

    if router_utils.HasReplaceAdvertisementFlags(args):
      mode, groups, prefixes = router_utils.ParseAdvertisements(
          messages=messages, resource_class=messages.RouterBgp, args=args)

      router_utils.PromptIfSwitchToDefaultMode(
          messages=messages,
          resource_class=messages.RouterBgp,
          existing_mode=existing.bgp.advertiseMode,
          new_mode=mode)

      attrs = {
          'advertiseMode': mode,
          'advertisedGroups': groups,
          'advertisedPrefixs': prefixes,
      }

      for attr, value in attrs.items():
        if value is not None:
          setattr(replacement.bgp, attr, value)

    if router_utils.HasIncrementalAdvertisementFlags(args):
      # This operation should only be run on custom mode routers.
      router_utils.ValidateCustomMode(
          messages=messages,
          resource_class=messages.RouterBgp,
          resource=replacement.bgp)

      # These arguments are guaranteed to be mutually exclusive in args.
      if args.add_advertisement_groups:
        groups_to_add = router_utils.ParseGroups(
            resource_class=messages.RouterBgp,
            groups=args.add_advertisement_groups)
        replacement.bgp.advertisedGroups.extend(groups_to_add)

      if args.remove_advertisement_groups:
        groups_to_remove = router_utils.ParseGroups(
            resource_class=messages.RouterBgp,
            groups=args.remove_advertisement_groups)
        router_utils.RemoveGroupsFromAdvertisements(
            messages=messages,
            resource_class=messages.RouterBgp,
            resource=replacement.bgp,
            groups=groups_to_remove)

      if args.add_advertisement_ranges:
        ip_ranges_to_add = router_utils.ParseIpRanges(
            messages=messages, ip_ranges=args.add_advertisement_ranges)
        replacement.bgp.advertisedPrefixs.extend(ip_ranges_to_add)

      if args.remove_advertisement_ranges:
        router_utils.RemoveIpRangesFromAdvertisements(
            messages=messages,
            resource_class=messages.RouterBgp,
            resource=replacement.bgp,
            ip_ranges=args.remove_advertisement_ranges)

    request_type = messages.ComputeRoutersPatchRequest
    include_fields = [
        'bgp.advertisedGroups',
        'bgp.advertisedPrefixs',
    ]
    with holder.client.apitools_client.IncludeFields(include_fields):
      resource = service.Patch(
          request_type(
              project=ref.project,
              region=ref.region,
              router=ref.Name(),
              routerResource=replacement))

    return resource


UpdateAlpha.detailed_help = {
    'DESCRIPTION': """
        *{command}* is used to update a Google Compute Engine router.
        """,
}
