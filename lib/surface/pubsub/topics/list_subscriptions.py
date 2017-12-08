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
"""Cloud Pub/Sub topics list_subscriptions command."""
from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import util


class ListSubscriptions(base.ListCommand):
  """Lists Cloud Pub/Sub subscriptions from a given topic.

  Lists all of the Cloud Pub/Sub subscriptions attached to the given topic and
  that match the given filter.
  """

  detailed_help = {
      'EXAMPLES': """\
          To filter results by subscription name
          (ie. only show subscription 'mysubs'), run:

            $ {command} --topic mytopic --filter=subscriptionId:mysubs

          To combine multiple filters (with AND or OR), run:

            $ {command} --topic mytopic --filter="subscriptionId:mysubs1 AND subscriptionId:mysubs2"

          To filter subscriptions that match an expression:

            $ {command} --topic mytopic --filter="subscriptionId:subs_*"
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('yaml')
    parser.display_info.AddUriFunc(util.SubscriptionUriFunc)

    flags.AddTopicResourceArg(parser, 'to list subscriptions for.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      Subscriptions paths that match the regular expression in args.name_filter.
    """
    client = topics.TopicsClient()

    topic_ref = util.ParseTopic(args.topic)
    for topic_sub in client.ListSubscriptions(topic_ref,
                                              page_size=args.page_size):
      yield util.ListTopicSubscriptionDisplayDict(topic_sub)

