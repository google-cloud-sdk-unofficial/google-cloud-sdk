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
"""Cloud Pub/Sub subscription pull command."""
from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import util


class Pull(base.ListCommand):
  """Pulls one or more Cloud Pub/Sub messages from a subscription.

  Returns one or more messages from the specified Cloud Pub/Sub subscription,
  if there are any messages enqueued.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
      table[box](
        message.data.decode(base64),
        message.messageId,
        message.attributes.list(separator='\n'),
        ackId.if(NOT auto_ack)
      )
    """)
    flags.AddSubscriptionResourceArg(parser, 'to pull messages from.')
    flags.AddPullFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A PullResponse message with the response of the Pull operation.
    """
    client = subscriptions.SubscriptionsClient()

    subscription_ref = util.ParseSubscription(args.subscription)
    pull_response = client.Pull(subscription_ref, args.max_messages)

    if args.auto_ack and pull_response.receivedMessages:
      ack_ids = [message.ackId for message in pull_response.receivedMessages]
      client.Ack(ack_ids, subscription_ref)

    return pull_response.receivedMessages
