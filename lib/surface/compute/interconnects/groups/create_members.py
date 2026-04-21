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

"""Command for creating new member interconnects in an interconnect group."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects.groups import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.interconnects import flags as interconnect_flags
from googlecloudsdk.command_lib.compute.interconnects.groups import flags
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION': (
        """\
        *{command}* is used to create new member interconnects in an
        interconnect group.

        For an example, refer to the *EXAMPLES* section below.
        """
    ),
    'DEFAULTABLE PER-INTERCONNECT FLAGS': (
        """\
        All flags except `--intent-mismatch-behavior` in the *OPTIONAL FLAGS*
        section are defaultable per-interconnect. This means that you can
        set a default value by using these flags, or you can override the value
        for each interconnect by using the `--interconnect` flag.

        Furthermore, if the default values for the following flags are not
        specified, then they must be specified per-interconnect in the
        `--interconnect` flag:

        * `--facility`
        * `--interconnect-type`
        * `--link-type`
        * `--requested-link-count`
        """
    ),
    'EXAMPLES': (
        """\
        To create interconnects interconnect1 and interconnect2 in interconnect
        group example-interconnect-group, run:

          $ {command} example-interconnect-group --interconnect-type=DEDICATED
          --link-type=LINK_TYPE_ETHERNET_10G_LR --requested-link-count=1
          --facility=iad-1 --interconnect="name=interconnect1"
          --interconnect="name=interconnect2,facility=iad-5467"

        Note that facility is required for each member interconnect.
        interconnect1's facility is set to the default value iad-1 and
        interconnect2's facility is overridden to iad-5467 in the
        `--interconnect` flag.
        """
    ),
}

# Interconnect Flags
_FACILITY = 'facility'
_DESCRIPTION = 'description'
_NAME = 'name'
_LINK_TYPE = 'link-type'
_REQUESTED_LINK_COUNT = 'requested-link-count'
_INTERCONNECT_TYPE = 'interconnect-type'
_ADMIN_ENABLED = 'admin-enabled'
_NO_ADMIN_ENABLED = 'no-admin-enabled'
_NOC_CONTACT_EMAIL = 'noc-contact-email'
_CUSTOMER_NAME = 'customer-name'
_REMOTE_LOCATION = 'remote-location'
_REQUESTED_FEATURES = 'requested-features'


def _CheckRequiredFlagPresent(args, ic_args, flag_name):
  """Checks that flag is present in template args or interconnect args."""
  flag_present_in_template = getattr(args, flag_name.replace('-', '_'))
  if not flag_present_in_template and flag_name not in ic_args:
    raise exceptions.RequiredArgumentException(
        '--' + flag_name,
        flag_name
        + ' must be provided either in template via --'
        + flag_name
        + ' or for each member interconnect via --interconnect flag.',
    )


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA,
    base.ReleaseTrack.PREVIEW,
)
class CreateMembers(base.UpdateCommand):
  """Create new member interconnects in a Compute Engine interconnect group.

  *{command}* creates new member interconnects in a Compute Engine interconnect
  group.
  """

  INTERCONNECT_GROUP_ARG = None
  REMOTE_LOCATION_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.INTERCONNECT_GROUP_ARG = flags.InterconnectGroupArgument(plural=False)
    cls.INTERCONNECT_GROUP_ARG.AddArgument(
        parser, operation_type='create members'
    )
    flags.AddMemberInterconnectsForCreateMembers(parser)
    flags.AddFacility(parser)
    flags.AddRemoteLocation(parser)
    flags.AddIntentMismatchBehavior(parser)
    interconnect_flags.AddCreateArgsForInterconnectGroupsCreateMembers(
        parser, required=False
    )

  def Collection(self):
    return 'compute.interconnectGroups'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.INTERCONNECT_GROUP_ARG.ResolveAsResource(args, holder.resources)
    project = properties.VALUES.core.project.GetOrFail()

    interconnect_group = client.InterconnectGroup(
        ref, project, compute_client=holder.client, resources=holder.resources
    )

    messages = holder.client.messages
    template_interconnect = (
        interconnect_group.MakeInterconnectGroupsCreateMembersInterconnectInput(
            facility=args.facility,
            description=args.description,
            name=None,
            link_type=flags.GetLinkType(messages, args.link_type),
            requested_link_count=args.requested_link_count,
            interconnect_type=flags.GetInterconnectType(
                messages, args.interconnect_type
            ),
            admin_enabled=args.admin_enabled,
            noc_contact_email=args.noc_contact_email,
            customer_name=args.customer_name,
            remote_location=args.remote_location,
            requested_features=flags.GetRequestedFeatures(
                messages, args.requested_features
            ),
        )
    )
    member_interconnects = []
    for ic_args in args.interconnect:
      _CheckRequiredFlagPresent(args, ic_args, _FACILITY)
      _CheckRequiredFlagPresent(args, ic_args, _INTERCONNECT_TYPE)
      _CheckRequiredFlagPresent(args, ic_args, _LINK_TYPE)
      _CheckRequiredFlagPresent(args, ic_args, _REQUESTED_LINK_COUNT)
      if _ADMIN_ENABLED in ic_args:
        admin_enabled = True
      elif _NO_ADMIN_ENABLED in ic_args:
        admin_enabled = False
      else:
        admin_enabled = None
      member_interconnects.append(
          interconnect_group.MakeInterconnectGroupsCreateMembersInterconnectInput(
              facility=ic_args.get(_FACILITY),
              description=ic_args.get(_DESCRIPTION),
              name=ic_args.get(_NAME),
              link_type=flags.GetLinkType(messages, ic_args.get(_LINK_TYPE)),
              requested_link_count=ic_args.get(_REQUESTED_LINK_COUNT),
              interconnect_type=flags.GetInterconnectType(
                  messages, ic_args.get(_INTERCONNECT_TYPE)
              ),
              admin_enabled=admin_enabled,
              noc_contact_email=ic_args.get(_NOC_CONTACT_EMAIL),
              customer_name=ic_args.get(_CUSTOMER_NAME),
              remote_location=ic_args.get(_REMOTE_LOCATION),
              requested_features=flags.GetRequestedFeatures(
                  messages, ic_args.get(_REQUESTED_FEATURES)
              ),
          )
      )

    return interconnect_group.CreateMembers(
        intent_mismatch_behavior=flags.GetIntentMismatchBehavior(
            messages, args.intent_mismatch_behavior
        ),
        template_interconnect=template_interconnect,
        member_interconnects=member_interconnects,
    )


CreateMembers.detailed_help = DETAILED_HELP
