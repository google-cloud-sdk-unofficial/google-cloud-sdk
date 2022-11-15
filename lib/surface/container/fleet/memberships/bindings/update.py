# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to update Membership Binding information."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update the Binding in a Membership.

  This command can fail for the following reasons:
  * The Membership specified does not exist.
  * The Binding does not exist in the Membership.
  * The caller does not have permission to access the Membership/Binding.
  * The Scope specified does not exist.
  * The caller did not specify the location (--location) if referring to
  location other than global.

  ## EXAMPLES

  To update the binding `BINDING_NAME` in global membership `MEMBERSHIP_NAME`
  in the active project:

    $ {command} BINDING_NAME --membership=MEMBERSHIP_NAME

  To update a Binding `BINDING_NAME` associated with regional membership
  `MEMBERSHIP_NAME`, provide the location LOCATION_NAME for the Membership where
  the Binding belongs along with membership name and associated
  Scope `SCOPE_NAME`.

  $ {command} BINDING_NAME --membership MEMBERSHIP_NAME --scope SCOPE_NAME
    --location=LOCATION_NAME

  """

  @staticmethod
  def Args(parser):
    resources.AddMembershipBindingResourceArg(
        parser,
        api_version='v1alpha',
        binding_help=('Name of the Membership Binding to be updated.'
                      'Must comply with RFC 1123 (up to 63 characters, '
                      'alphanumeric and \'-\')'))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--fleet',
        type=bool,
        help='Bindings for all the membership related scopes in the fleet would be updated.',
    )
    group.add_argument(
        '--scope',
        type=str,
        help='Scope related to the Binding.',
    )

  def Run(self, args):
    fleetclient = client.FleetClient(release_track=base.ReleaseTrack.ALPHA)
    mask = []
    for flag in ['fleet', 'scope']:
      if args.IsKnownAndSpecified(flag):
        mask.append(flag)
    return fleetclient.UpdateMembershipBinding(
        resources.MembershipBindingResourceName(args),
        scope=args.scope,
        fleet=args.fleet,
        mask=','.join(mask))
