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
"""Command for deleting a Cloud Security Command Center notification config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import util
from googlecloudsdk.command_lib.scc.notifications import flags as notifications_flags
from googlecloudsdk.command_lib.scc.notifications import notification_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.generated_clients.apis.securitycenter.v1 import securitycenter_v1_messages


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Delete(base.DeleteCommand):
  """Delete a Cloud Security Command Center notification config."""

  detailed_help = {
      'DESCRIPTION': """\
      Delete a Cloud Security Command Center notification config.
      """,
      'EXAMPLES': """\
      Delete notification config 'my-config' from organization 123

        $ {command} my-config --organization=123
        $ {command} organizations/123/notificationConfigs/my-config

      Delete notification config 'my-config' from folder 456

        $ {command} my-config --folder=456
        $ {command} folders/456/notificationConfigs/my-config

      Delete notification config 'my-config' from project 789

        $ {command} my-config --project=789
        $ {command} projects/789/notificationConfigs/my-config
      """,
      'API REFERENCE': """\
      This command uses the securitycenter/v1 API. The full documentation for
      this API can be found at: https://cloud.google.com/security-command-center
      """,
  }

  @staticmethod
  def Args(parser):

    notifications_flags.AddParentGroup(parser)
    notifications_flags.AddNotificationConfigPositionalArgument(parser)

  def Run(self, args):
    req = (
        securitycenter_v1_messages.SecuritycenterOrganizationsNotificationConfigsDeleteRequest()
    )

    # Prompt user to confirm deletion.
    console_io.PromptContinue(
        message='Are you sure you want to delete a notification config?\n',
        cancel_on_no=True,
    )

    # Validate mutex after prompt.
    parent = util.GetParentFromNamedArguments(args)
    notification_util.ValidateMutexOnConfigIdAndParent(args, parent)
    req.name = notification_util.GetNotificationConfigName(args)

    client = apis.GetClientInstance('securitycenter', 'v1')
    result = client.organizations_notificationConfigs.Delete(req)
    log.status.Print('Deleted.')
    return result
