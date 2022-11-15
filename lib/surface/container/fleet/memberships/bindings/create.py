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
"""Command to create a Membership Binding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Membership Binding.

  This command can fail for the following reasons:
  * The Membership Binding already exists.
  * The caller does not have permission to access the given Membership.
  * The Scope or the Membership does not exist.
  * The caller did not specify the location (--location) if referring to
  location other than global.

  ## EXAMPLES

  To create a membership binding `BINDING_NAME` in global membership
  `MEMBERSHIP_NAME` for scope `SCOPE_NAME`, run:

    $ {command} BINDING_NAME --membership MEMBERSHIP_NAME --scope SCOPE_NAME

  To create a Binding `BINDING_NAME` associated with regional membership
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
        binding_help=('Name of the membership Binding to be created.'
                      'Must comply with RFC 1123 (up to 63 characters, '
                      'alphanumeric and \'-\')'))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--fleet',
        type=bool,
        help='Membership Binding is created for all the Scopes in the Fleet for given Membership.',
    )
    group.add_argument(
        '--scope',
        type=str,
        help='Scope to assign.',
    )

  def Run(self, args):
    fleetclient = client.FleetClient(release_track=base.ReleaseTrack.ALPHA)
    return fleetclient.CreateMembershipBinding(
        resources.MembershipBindingResourceName(args),
        fleet=args.fleet,
        scope=args.scope)
