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

"""permissions describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import dataclasses

from googlecloudsdk.api_lib.accesscontextmanager import supported_permissions
from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import flags
from googlecloudsdk.command_lib.iam import iam_util


@dataclasses.dataclass
class SupportedPermission:
  role_name: str
  support_status: str
  supported_permissions: str

  def __eq__(self, other: 'SupportedPermission') -> bool:
    return (
        self.role_name == other.role_name
        and self.support_status == other.support_status
        and self.supported_permissions == other.supported_permissions
    )


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeSupportedPermissions(base.DescribeCommand):
  """Describes which permissions in a provided role are supported by [VPC Service Controls]."""

  _API_VERSION = 'v1alpha'
  detailed_help = {
      'brief': (
          'Describes which permissions in a provided role are supported by VPC'
          ' Service Controls'
      ),
      'DESCRIPTION': (
          'Describes which permissions in a provided role are supported by VPC'
          ' Service Controls.'
      ),
      'EXAMPLES': """\
  To describe which permissions VPC Service Controls supports for a provided role, run:

    $ {command} roles/example.role.name

  This command prints out a list of all supported permissions in a tabular form:

    ROLE NAME                    SUPPORT STATUS              SUPPORTED PERMISSIONS
    roles/example.role.name      SUPPORTED                   example.permission.one
                                                             example.permission.two

  To describe which permissions VPC Service Controls supports for a custom role, run:

    $ {command} TestCustomRole --project=example-project

  NOTE: If the provided role is a custom role, an organization or project must be specified.

  This command prints out a list of all supported permissions in a tabular form:

    ROLE NAME                                      SUPPORT STATUS              SUPPORTED PERMISSIONS
    projects/example-project/roles/TestCustomRole  SUPPORTED                   example.permission.one

  """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    flags.AddParentFlags(parser, 'describe', required=False)
    flags.GetRoleFlag('describe').AddToParser(parser)

    parser.display_info.AddFormat(
        'table(role_name, support_status, supported_permissions)'
    )

  def Run(self, args):
    """Run 'access-context-manager supported-permissions describe ROLE'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      An object of type SupportedPermission describing which permissions in the
      role are supported by VPC Service Controls.
    """
    # Get the role from IAM to understand which permissions are included in it.
    role_name = iam_util.GetRoleName(args.organization, args.project, args.role)
    iam_client, iam_messages = util.GetClientAndMessages()
    res = iam_client.organizations_roles.Get(
        iam_messages.IamOrganizationsRolesGetRequest(
            name=role_name,
        )
    )
    iam_permissions_set = set(res.includedPermissions)

    # Get the supported permissions from ACM.
    acm_client = supported_permissions.Client(version=self._API_VERSION)

    # iterate through the supported permissions in ACM and find the ones that
    # are in the role.
    role_permissions_supported_by_acm = []
    for acm_supported_permission in acm_client.List(page_size=100, limit=None):
      if acm_supported_permission in iam_permissions_set:
        role_permissions_supported_by_acm.append(acm_supported_permission)
      if len(role_permissions_supported_by_acm) == len(iam_permissions_set):
        break

    if len(role_permissions_supported_by_acm) == len(iam_permissions_set):
      support_status = 'SUPPORTED'
    elif role_permissions_supported_by_acm:
      support_status = 'PARTIALLY_SUPPORTED'
    else:
      support_status = 'NOT_SUPPORTED'

    return [
        SupportedPermission(
            role_name,
            support_status,
            '\n'.join(role_permissions_supported_by_acm),
        )
    ]
