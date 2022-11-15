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
"""Command to create a fleet namespace RBAC RoleBinding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create an RBAC RoleBinding.

  This command can fail for the following reasons:
  * The RBAC RoleBinding already exists.
  * The caller does not have permission to access the given namespace.

  ## EXAMPLES

  To create an admin RBAC RoleBinding `RBRB` in namespace `NAMESPACE` for user
  `person@google.com`, run:

    $ {command} RBRB --namespace=NAMESPACE --role=admin
    --user=person@google.com

  To create a viewer RBAC RoleBinding `RBRB` in namespace `NAMESPACE` for group
  `people@google.com`, run:

    $ {command} RBRB --namespace=NAMESPACE --role=viewer
    --group=people@google.com
  """

  @staticmethod
  def Args(parser):
    resources.AddRBACResourceArg(
        parser,
        api_version='v1alpha',
        rbacrb_help=('Name of the RBAC RoleBinding to be created. '
                     'Must comply with RFC 1123 (up to 63 characters, '
                     'alphanumeric and \'-\')'))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--user',
        type=str,
        help='User for the RoleBinding.',
    )
    group.add_argument(
        '--group',
        type=str,
        help='Group for the RoleBinding.',
    )
    parser.add_argument(
        '--role',
        required=True,
        choices=['admin', 'edit', 'view'],
        help='Role to assign.',
    )

  def Run(self, args):
    fleetclient = client.FleetClient(release_track=base.ReleaseTrack.ALPHA)
    return fleetclient.CreateRBACRoleBinding(
        resources.RBACResourceName(args),
        role=args.role,
        user=args.user,
        group=args.group)
