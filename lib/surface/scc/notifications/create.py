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

"""Command for creating a Cloud Security Command Center NotificationConfig."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc import securitycenter_client as sc_client
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import util
from googlecloudsdk.command_lib.scc.notifications import flags as notifications_flags
from googlecloudsdk.command_lib.scc.notifications import notification_util
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.securitycenter.v1 import securitycenter_v1_messages


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Create(base.CreateCommand):
  """Create a Cloud Security Command Center notification config."""

  detailed_help = {
      'DESCRIPTION': """\
      Create a Cloud Security Command Center notification config.
      """,
      'EXAMPLES': """\
      Create a notification config test-config under organization 123 for
      findings for pubsub-topic projects/test-project/topics/notification-test
      with a filter on resource name:

        $ {command} test-config --organization=123
          --pubsub-topic=projects/test-project/topics/notification-test
          --filter="resource_name: \\"a\\""
        $ {command} organizations/123/notificationConfigs/test-config
          --pubsub-topic=projects/test-project/topics/notification-test
          --filter="resource_name: \\"a\\""

      Create a notification config test-config under folder 456 for findings for
      pubsub-topic projects/test-project/topics/notification-test with a filter
      on resource name:

        $ {command} test-config --folder=456
          --pubsub-topic=projects/test-project/topics/notification-test
          --filter="resource_name: \\"a\\""
        $ {command} folders/456/notificationConfigs/test-config
          --pubsub-topic=projects/test-project/topics/notification-test
          --filter="resource_name: \\"a\\""

      Create a notification config test-config under project 789 for findings
      for pubsub-topic projects/test-project/topics/notification-test with a
      filter on resource name:

        $ {command} test-config --project=789
          --pubsub-topic=projects/test-project/topics/notification-test
          --filter="resource_name: \\"a\\""
        $ {command} projects/789/notificationConfigs/test-config
          --pubsub-topic=projects/test-project/topics/notification-test
          --filter="resource_name: \\"a\\""
      """,
      'API REFERENCE': """\
      This command uses the securitycenter/v1 API. The full documentation for
      this API can be found at: https://cloud.google.com/security-command-center
      """,
  }

  @staticmethod
  def Args(parser):

    notifications_flags.PUBSUB_TOPIC_REQUIRED_FLAG.AddToParser(parser)
    notifications_flags.DESCRIPTION_FLAG.AddToParser(parser)
    notifications_flags.FILTER_FLAG.AddToParser(parser)

    notifications_flags.AddNotificationConfigPositionalArgument(parser)
    notifications_flags.AddParentGroup(parser)

  def Run(self, args):
    req = (
        securitycenter_v1_messages.SecuritycenterOrganizationsNotificationConfigsCreateRequest()
    )
    parent = util.GetParentFromNamedArguments(args)

    notification_util.ValidateMutexOnConfigIdAndParent(args, parent)
    config_name = notification_util.GetNotificationConfigName(args)

    req.parent = notification_util.GetParentFromResourceName(config_name)
    req.configId = _GetNotificationConfigId(config_name)

    messages = sc_client.GetMessages('v1')
    req.notificationConfig = messages.NotificationConfig()
    req.notificationConfig.name = args.NOTIFICATIONCONFIGID
    req.notificationConfig.description = args.description
    req.notificationConfig.pubsubTopic = args.pubsub_topic

    # Set the Streaming Config inside Notification Config.
    streaming_config = messages.StreamingConfig()
    if args.filter is None:
      streaming_config.filter = ''
    else:
      streaming_config.filter = args.filter
    req.notificationConfig.streamingConfig = streaming_config

    client = apis.GetClientInstance('securitycenter', 'v1')
    result = client.organizations_notificationConfigs.Create(req)
    log.status.Print('Created.')
    return result.name


def _GetNotificationConfigId(resource_name):
  params_as_list = resource_name.split('/')
  return params_as_list[3]
