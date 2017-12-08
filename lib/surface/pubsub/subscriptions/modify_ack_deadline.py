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
"""Cloud Pub/Sub subscription modify command."""
from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import util


class ModifyAckDeadline(base.Command):
  """Modifies the ACK deadline for a specific Cloud Pub/Sub message.

  This method is useful to indicate that more time is needed to process a
  message by the subscriber, or to make the message available for
  redelivery if the processing was interrupted.
  """

  @staticmethod
  def Args(parser):
    flags.AddSubscriptionResourceArg(parser, 'messages belong to.')
    flags.AddAckIdFlag(parser, 'modify the deadline for.')
    flags.AddAckDeadlineFlag(parser, required=True)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Display dictionary with information about the new ACK deadline seconds
      for the given subscription and ackId.
    """
    client = subscriptions.SubscriptionsClient()

    subscription_ref = util.ParseSubscription(args.subscription)
    client.ModifyAckDeadline(subscription_ref, args.ack_id, args.ack_deadline)

    return {'subscriptionId': subscription_ref.RelativeName(),
            'ackId': args.ack_id,
            'ackDeadlineSeconds': args.ack_deadline}
