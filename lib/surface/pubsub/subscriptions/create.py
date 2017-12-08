# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Cloud Pub/Sub subscription create command."""

import json
from apitools.base.py import exceptions as api_ex

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_projector


class Create(base.Command):
  """Creates one or more Cloud Pub/Sub subscriptions.

  Creates one or more Cloud Pub/Sub subscriptions for a given topic.
  The new subscription defaults to a PULL subscription unless a push endpoint
  is specified.
  """

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""

    parser.add_argument('subscription', nargs='+',
                        help='One or more subscriptions to create.')

    parser.add_argument(
        '--topic', required=True,
        help=('The name of the topic from which this subscription is receiving'
              ' messages. Each subscription is attached to a single topic.'))

    parser.add_argument(
        '--topic-project', default='',
        help=('The name of the project the provided topic belongs to.'
              ' If not set, it defaults to the currently selected'
              ' cloud project.'))

    parser.add_argument(
        '--ack-deadline', type=int, default=10,
        help=('The number of seconds the system will wait for a subscriber to'
              ' acknowledge receiving a message before re-attempting'
              ' delivery.'))

    parser.add_argument(
        '--push-endpoint',
        help=('A URL to use as the endpoint for this subscription.'
              ' This will also automatically set the subscription'
              ' type to PUSH.'))

  def Collection(self):
    return util.SUBSCRIPTIONS_COLLECTION

  @util.MapHttpError
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      A serialized object (dict) describing the results of the operation.
      This description fits the Resource described in the ResourceRegistry under
      'pubsub.projects.topics'.
    """
    msgs = self.context['pubsub_msgs']
    pubsub = self.context['pubsub']

    topic_project = ''
    if args.topic_project:
      topic_project = projects_util.ParseProject(args.topic_project).Name()
    topic_name = resources.Parse(args.topic,
                                 collection=util.TOPICS_COLLECTION).Name()

    for subscription in args.subscription:
      subscription_name = resources.Parse(
          subscription, collection=util.SUBSCRIPTIONS_COLLECTION).Name()
      create_req = msgs.Subscription(
          name=util.SubscriptionFormat(subscription_name),
          topic=util.TopicFormat(topic_name, topic_project),
          ackDeadlineSeconds=args.ack_deadline)
      if args.push_endpoint:
        create_req.pushConfig = msgs.PushConfig(pushEndpoint=args.push_endpoint)

      try:
        yield SubscriptionDisplayDict(
            pubsub.projects_subscriptions.Create(create_req))
      except api_ex.HttpError as exc:
        yield SubscriptionDisplayDict(
            subscription, json.loads(exc.content)['error']['message'])


def SubscriptionDisplayDict(subscription, error_msg=''):
  """Creates a serializable from a Cloud Pub/Sub create Subscription operation.

  Args:
    subscription: (Cloud Pub/Sub Subscription) Subscription to be serialized.
    error_msg: (string) An error message to be added to the serialized
               result, if any.
  Returns:
    A serialized object representing a Cloud Pub/Sub Subscription
    create operation.
  """
  subs_create_dict = resource_projector.MakeSerializable(subscription)

  push_endpoint = ''
  subscription_type = 'pull'
  if subscription.pushConfig:
    push_endpoint = subscription.pushConfig.pushEndpoint
    subscription_type = 'push'
    del subs_create_dict['pushConfig']

  success = True
  if error_msg:
    success = False

  subs_create_dict['subscriptionId'] = subscription.name
  subs_create_dict['type'] = subscription_type
  subs_create_dict['topic'] = subscription.topic
  subs_create_dict['pushEndpoint'] = push_endpoint
  subs_create_dict['success'] = success
  subs_create_dict['reason'] = error_msg
  del subs_create_dict['name']

  return subs_create_dict
