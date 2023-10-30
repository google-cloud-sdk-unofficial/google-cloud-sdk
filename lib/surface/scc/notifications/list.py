# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command for listing Cloud Security Command Center Notification Configs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import flags as scc_flags
from googlecloudsdk.command_lib.scc import util
from googlecloudsdk.generated_clients.apis.securitycenter.v1 import securitycenter_v1_messages as messages


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class List(base.ListCommand):
  """List Cloud Security Command Center notification configs."""

  detailed_help = {
      'DESCRIPTION': 'List Cloud Security Command Center notification configs.',
      'EXAMPLES': """\
      List notification configs from organization 123

        $ {command} 123
        $ {command} organizations/123

      List notification configs from folder 456

        $ {command} folders/456

      List notification configs from project 789

        $ {command} projects/789
      """,
      'API REFERENCE': """\
      This command uses the securitycenter/v1 API. The full documentation for
      this API can be found at: https://cloud.google.com/security-command-center
          """,
  }

  @staticmethod
  def Args(parser):
    # Remove URI flag.
    base.URI_FLAG.RemoveFromParser(parser)

    # Add shared flags and parent positional argument.
    scc_flags.AppendParentArg()[0].AddToParser(parser)

  def Run(self, args):
    request = (
        messages.SecuritycenterOrganizationsNotificationConfigsListRequest()
    )
    request.parent = util.GetParentFromPositionalArguments(args)
    request.pageSize = args.page_size

    client = apis.GetClientInstance('securitycenter', 'v1')

    # Automatically handle pagination. All notifications are returned regardless
    # of --page-size argument.
    return list_pager.YieldFromList(
        client.organizations_notificationConfigs,
        request,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='notificationConfigs',
    )
