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
"""Cloud Pub/Sub subscriptions ack command."""
from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import util


class Ack(base.Command):
  """Acknowledges one or more messages on the specified subscription.

  Acknowledges one or more messages as having been successfully received.
  If a delivered message is not acknowledged, Cloud Pub/Sub will attempt to
  deliver it again.
  """

  @staticmethod
  def Args(parser):
    flags.AddSubscriptionResourceArg(parser, 'to ACK messages on.')
    flags.AddAckIdFlag(parser, 'acknowledge.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Ack display dictionary with information about the acknowledged messages
      and related subscription.
    """
    client = subscriptions.SubscriptionsClient()

    subscription_ref = util.ParseSubscription(args.subscription)
    client.Ack(args.ack_id, subscription_ref)

    # Using this dict, instead of returning the AcknowledgeRequest directly,
    # to preserve the naming conventions for subscriptionId.
    return {'subscriptionId': subscription_ref.RelativeName(),
            'ackIds': args.ack_id}
