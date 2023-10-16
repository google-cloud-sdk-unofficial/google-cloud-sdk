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
"""Command for describing a Cloud Security Command Center NotificationConfig."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import util
from googlecloudsdk.command_lib.scc.notifications import notification_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.generated_clients.apis.securitycenter.v1 import securitycenter_v1_messages


class InvalidNotificationConfigError(core_exceptions.Error):
  """Exception raised for errors in the input."""


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Describe(base.DescribeCommand):
  """Describe a Cloud Security Command Center notification config."""

  detailed_help = {
      'DESCRIPTION': """\
      Describe a Cloud Security Command Center notification config.
      """,
      'EXAMPLES': """\
      Describe notification config 'my-config' from organization 123

          $ {command} notifications describe my-config \
              --organization=123
          $ {command} notifications describe \
              organizations/123/notificationConfigs/my-config

      Describe notification config 'my-config' from folder 456

          $ {command} notifications describe my-config \
              --folder=456
          $ {command} notifications describe \
              folders/456/notificationConfigs/my-config

      Describe notification config 'my-config' from project 789

          $ {command} notifications describe my-config \
              --project=789
          $ {command} notifications describe \
              projects/789/notificationConfigs/my-config
      """,
      'API REFERENCE': """\
      This command uses the securitycenter/v1 API. The full documentation for
      this API can be found at: https://cloud.google.com/security-command-center
      """,
  }

  @staticmethod
  def Args(parser):
    # Notification Config Id is a required argument.
    parser.add_argument(
        'NOTIFICATIONCONFIGID',
        metavar='NOTIFICATION_CONFIG_ID',
        help="""\
         The ID of the notification config. Formatted as
         "organizations/123/notificationConfigs/456" or just "456".
        """,
    )

    # Set org/folder/project as mutually exclusive group.
    resource_group = parser.add_group(required=False, mutex=True)
    resource_group.add_argument(
        '--organization',
        help="""\
            Organization where the notification config resides. Formatted as
            ``organizations/123'' or just ``123''.
            """,
    )
    resource_group.add_argument(
        '--folder',
        help="""\
            Folder where the notification config resides. Formatted as
            ``folders/456'' or just ``456''.
        """,
    )
    resource_group.add_argument(
        '--project',
        help="""\
            Project (ID or number) where the notification config resides.
            Formatted as ``projects/789'' or just ``789''.
        """,
    )

  def Run(self, args):
    req = (
        securitycenter_v1_messages.SecuritycenterOrganizationsNotificationConfigsGetRequest()
    )

    parent = util.GetParentFromNamedArguments(args)
    notification_util.ValidateMutexOnConfigIdAndParent(args, parent)
    req.name = notification_util.GetNotificationConfigName(args)

    client = apis.GetClientInstance('securitycenter', 'v1')
    result = client.organizations_notificationConfigs.Get(req)
    return result
