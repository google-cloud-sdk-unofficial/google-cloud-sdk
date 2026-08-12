# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Implementation of gcloud support support-event-subscriptions create."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base


_VERSION_MAP = {
    base.ReleaseTrack.GA: 'v2',
    base.ReleaseTrack.BETA: 'v2beta',
}


@base.UniverseCompatible
class Create(base.CreateCommand):
  """Create a support event subscription."""

  detailed_help = {
      'DESCRIPTION': (
          """
          *{command}* creates a support event subscription for an organization.
      """
      ),
      'EXAMPLES': (
          """
          To create a support event subscription for organization ``123456789'':

            $ {command} --organization=123456789 --pub-sub-topic=projects/my-project/topics/my-topic
      """
      ),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--organization',
        required=True,
        help='Organization ID for the support event subscription.',
    )
    parser.add_argument(
        '--pub-sub-topic',
        required=True,
        help=(
            'The name of the Pub/Sub topic to publish notifications to.'
            ' Format: projects/{project}/topics/{topic}'
        ),
    )

  def Run(self, args):
    """Execute the API call."""
    version = _VERSION_MAP.get(self.ReleaseTrack(), 'v2')
    client = apis.GetClientInstance('cloudsupport', version)
    messages = client.MESSAGES_MODULE

    parent = f'organizations/{args.organization}'
    subscription = messages.SupportEventSubscription(
        pubSubTopic=args.pub_sub_topic,
    )

    request = messages.CloudsupportOrganizationsSupportEventSubscriptionsCreateRequest(
        parent=parent,
        supportEventSubscription=subscription,
    )

    return client.organizations_supportEventSubscriptions.Create(request)
