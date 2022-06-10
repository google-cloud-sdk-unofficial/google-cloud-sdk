# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_ex

from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.api_lib.util import exceptions as util_ex
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util
import six

MESSAGE_FORMAT = """\
table[box](
  message.data.decode(base64).decode(utf-8),
  message.messageId,
  message.orderingKey,
  message.attributes.list(separator='\n'),
  deliveryAttempt,
  ackId.if(NOT auto_ack)
)
"""

MESSAGE_FORMAT_WITH_ACK_STATUS = """\
table[box](
  received_message.message.data.decode(base64).decode(utf-8),
  received_message.message.messageId,
  received_message.message.orderingKey,
  received_message.message.attributes.list(separator='\n'),
  received_message.deliveryAttempt,
  received_message.ackId.if(NOT auto_ack),
  ack_status.if(auto_ack)
)
"""


def _Run(args,
         max_messages,
         return_immediately=True,
         exactly_once_failure_handling=False):
  """Pulls messages from a subscription."""
  client = subscriptions.SubscriptionsClient()

  subscription_ref = args.CONCEPTS.subscription.Parse()
  pull_response = client.Pull(subscription_ref, max_messages,
                              return_immediately)

  failed_ack_ids = {}
  ack_ids_and_failure_reasons = []
  if args.auto_ack and pull_response.receivedMessages:
    ack_ids = [message.ackId for message in pull_response.receivedMessages]
    try:
      client.Ack(ack_ids, subscription_ref)
    except api_ex.HttpError as error:
      if not exactly_once_failure_handling:
        raise error

      exc = util_ex.HttpException(error)
      ack_ids_and_failure_reasons = util.ParseExactlyOnceErrorInfo(
          exc.payload.details)
      # If the failure doesn't have more information (specifically for exactly
      # once related failures), assume all the ack ids have failed with the
      # same status.
      if not ack_ids_and_failure_reasons:
        for ack_id in ack_ids:
          failed_ack_ids[ack_id] = 'FAILURE_' + six.text_type(error.status_code)

    if not failed_ack_ids:
      for ack_ids_and_failure_reason in ack_ids_and_failure_reasons:
        failed_ack_ids[ack_ids_and_failure_reason[
            'AckId']] = ack_ids_and_failure_reason['FailureReason']

  if not exactly_once_failure_handling:
    return pull_response.receivedMessages

  return_val = []
  for message in pull_response.receivedMessages:
    ack_status = 'SUCCESS'
    if message.ackId in failed_ack_ids:
      ack_status = failed_ack_ids[message.ackId]
    return_val.append({'received_message': message, 'ack_status': ack_status})
  return return_val


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Pull(base.ListCommand):
  """Pulls one or more Cloud Pub/Sub messages from a subscription."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Returns one or more messages from the specified Cloud Pub/Sub
          subscription, if there are any messages enqueued.

          By default, this command returns only one message from the
          subscription. Use the `--limit` flag to specify the max messages to
          return.

          Please note that this command is not guaranteed to return all the
          messages in your backlog or the maximum specified in the --limit
          argument.  Receiving fewer messages than available occasionally
          is normal."""
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(MESSAGE_FORMAT)
    resource_args.AddSubscriptionResourceArg(parser, 'to pull messages from.')
    flags.AddPullFlags(parser)

    base.LIMIT_FLAG.SetDefault(parser, 1)

  def Run(self, args):
    return _Run(args, args.limit)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class PullBeta(Pull):
  """Pulls one or more Cloud Pub/Sub messages from a subscription."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(MESSAGE_FORMAT_WITH_ACK_STATUS)
    resource_args.AddSubscriptionResourceArg(parser, 'to pull messages from.')
    flags.AddPullFlags(parser, add_deprecated=True, add_wait=True)

  def Run(self, args):
    if args.IsSpecified('limit'):
      if args.IsSpecified('max_messages'):
        raise exceptions.ConflictingArgumentsException('--max-messages',
                                                       '--limit')
      max_messages = args.limit
    else:
      max_messages = args.max_messages
    return_immediately = not args.wait if args.IsSpecified('wait') else True
    return _Run(
        args,
        max_messages,
        return_immediately,
        exactly_once_failure_handling=True)
