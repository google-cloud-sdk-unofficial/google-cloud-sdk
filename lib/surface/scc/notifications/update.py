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
"""Command for updating a Cloud Security Command Center NotificationConfig."""

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
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.securitycenter.v1 import securitycenter_v1_messages


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Update(base.UpdateCommand):
  """Update a Cloud Security Command Center notification config."""

  detailed_help = {
      'DESCRIPTION': """\
      Update a Cloud Security Command Center notification config.
      """,
      'EXAMPLES': """\
      Update all mutable fields under an organization parent my-config (description + pubsub topic + filter):

        $ {command} scc notifications update my-config --organization=123 \
            --description="New description" \
            --pubsub-topic="projects/22222/topics/newtopic"

        $ {command} scc notifications update \
            organizations/123/notificationConfigs/my-config \
            --description="New description" \
            --pubsub-topic="projects/22222/topics/newtopic"

      Update all mutable fields under a folder parent my-config (description + pubsub topic + filter):

        $ {command} scc notifications update my-config --folder=456 \
            --description="New description" \
            --pubsub-topic="projects/22222/topics/newtopic"

        $ {command} scc notifications update \
            folders/456/notificationConfigs/my-config \
            --description="New description" \
            --pubsub-topic="projects/22222/topics/newtopic"

      Update all mutable fields under a project parent my-config (description + pubsub topic + filter):

        $ {command} scc notifications update my-config --project=789 \
            --description="New description" \
            --pubsub-topic="projects/22222/topics/newtopic"

        $ {command} scc notifications update \
            projects/789/notificationConfigs/my-config \
            --description="New description" \
            --pubsub-topic="projects/22222/topics/newtopic"

      Update my-config's description

        $ {command} my-config --organization=123 --description="New description"

        $ {command} organizations/123/notificationConfigs/my-config
        --description="New description"

      Update my-config's pubsub-topic

        $ {command} my-config --organization=123
        --pubsub-topic="projects/22222/topics/newtopic"

        $ {command} organizations/123/notificationConfigs/my-config
        --pubsub-topic="projects/22222/topics/newtopic"

      Update my-config's filter

        $ {command} my-config --organization=123 --filter='state = \\"ACTIVE\\"'

        $ {command} organizations/123/notificationConfigs/my-config
        --filter='state = \\"ACTIVE\\"'
      """,
      'API REFERENCE': """\
      This command uses the securitycenter/v1 API. The full documentation for
      this API can be found at: https://cloud.google.com/security-command-center
      """,
  }

  @staticmethod
  def Args(parser):

    notifications_flags.DESCRIPTION_FLAG.AddToParser(parser)
    notifications_flags.FILTER_FLAG_LONG_DESCRIPTION.AddToParser(parser)
    notifications_flags.PUBSUB_TOPIC_OPTIONAL_FLAG.AddToParser(parser)

    notifications_flags.AddNotificationConfigPositionalArgument(parser)
    notifications_flags.AddParentGroup(parser)

    parser.display_info.AddFormat(properties.VALUES.core.default_format.Get())

  def Run(self, args):
    req = (
        securitycenter_v1_messages.SecuritycenterOrganizationsNotificationConfigsPatchRequest()
    )

    parent = util.GetParentFromNamedArguments(args)
    notification_util.ValidateMutexOnConfigIdAndParent(args, parent)
    req.name = notification_util.GetNotificationConfigName(args)

    computed_update_mask = []
    req.notificationConfig = securitycenter_v1_messages.NotificationConfig()
    if args.IsKnownAndSpecified('description'):
      computed_update_mask.append('description')
      req.notificationConfig.description = args.description
    if args.IsKnownAndSpecified('pubsub_topic'):
      computed_update_mask.append('pubsubTopic')
      req.notificationConfig.pubsubTopic = args.pubsub_topic
    if args.IsKnownAndSpecified('filter'):
      computed_update_mask.append('streamingConfig.filter')
      streaming_config = securitycenter_v1_messages.StreamingConfig()
      streaming_config.filter = args.filter
      req.notificationConfig.streamingConfig = streaming_config

    # User may not supply an updateMask.
    req.updateMask = ','.join(computed_update_mask)

    # Set the args' filter to None to avoid downstream naming conflicts.
    args.filter = None

    client = apis.GetClientInstance('securitycenter', 'v1')
    result = client.organizations_notificationConfigs.Patch(req)
    log.status.Print('Updated.')
    return result
