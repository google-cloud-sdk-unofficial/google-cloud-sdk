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
"""Cloud Pub/Sub subscriptions create command."""
from apitools.base.py import exceptions as api_ex

from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import log


def _ArgsBeta(parser):
  """Registers flags for this command."""

  parser.add_argument('subscription', nargs='+',
                      help='One or more subscriptions to create.')

  parser.add_argument(
      '--topic', required=True,
      help=('The name of the topic from which this subscription is receiving'
            ' messages. Each subscription is attached to a single topic.'))

  parser.add_argument(
      '--topic-project',
      help=('The name of the project the provided topic belongs to.'
            ' If not set, it defaults to the currently selected'
            ' cloud project.'))

  parser.add_argument(
      '--ack-deadline', type=int,
      help=('The number of seconds the system will wait for a subscriber to'
            ' acknowledge receiving a message before re-attempting'
            ' delivery.'))

  parser.add_argument(
      '--push-endpoint',
      help=('A URL to use as the endpoint for this subscription.'
            ' This will also automatically set the subscription'
            ' type to PUSH.'))


def _ArgsAlpha(parser):
  """Registers flags for this command that are available only in Alpha."""

  parser.add_argument(
      '--retain-acked-messages',
      action='store_true',
      default=None,
      help=('Whether or not to retain acknowledged messages.  If true,'
            ' messages are not expunged from the subscription\'s backlog'
            ' until they fall out of the --message-retention-duration'
            ' window.'))

  parser.add_argument(
      '--message-retention-duration',
      type=arg_parsers.Duration(),
      help=('How long to retain unacknowledged messages in the'
            ' subscription\'s backlog, from the moment a message is'
            ' published.  If --retain-acked-messages is true, this also'
            ' configures the retention of acknowledged messages.  The default'
            ' value is 7 days, the minimum is 10 minutes, and the maximum is'
            ' 7 days.  Valid values are strings of the form INTEGER[UNIT],'
            ' where UNIT is one of "s", "m", "h", and "d" for seconds,'
            ' seconds, minutes, hours, and days, respectively.  If the unit'
            ' is omitted, seconds is assumed.'))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Creates one or more Cloud Pub/Sub subscriptions.

  Creates one or more Cloud Pub/Sub subscriptions for a given topic.
  The new subscription defaults to a PULL subscription unless a push endpoint
  is specified.
  """

  @staticmethod
  def Args(parser):
    _ArgsBeta(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      A serialized object (dict) describing the results of the operation.
      This description fits the Resource described in the ResourceRegistry under
      'pubsub.projects.subscriptions'.

    Raises:
      util.RequestFailedError: if any of the requests to the API failed.
    """
    client = subscriptions.SubscriptionsClient()

    topic_ref = util.ParseTopic(args.topic, args.topic_project)
    push_config = util.ParsePushConfig(args.push_endpoint)
    retain_acked_messages = getattr(args, 'retain_acked_messages', None)
    retention_duration = getattr(args, 'message_retention_duration', None)
    if retention_duration:
      retention_duration = util.FormatDuration(retention_duration)

    failed = []
    for subscription_name in args.subscription:
      subscription_ref = util.ParseSubscription(subscription_name)

      try:
        result = client.Create(subscription_ref, topic_ref, args.ack_deadline,
                               push_config, retain_acked_messages,
                               retention_duration)
      except api_ex.HttpError as error:
        exc = exceptions.HttpException(error)
        log.CreatedResource(subscription_ref.RelativeName(),
                            kind='subscription',
                            failed=exc.payload.status_message)
        failed.append(subscription_name)
        continue

      result = util.SubscriptionDisplayDict(result)
      log.CreatedResource(subscription_ref.RelativeName(), kind='subscription')

      yield result

    if failed:
      raise util.RequestsFailedError(failed, 'create')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Creates one or more Cloud Pub/Sub subscriptions.

  Creates one or more Cloud Pub/Sub subscriptions for a given topic.
  The new subscription defaults to a PULL subscription unless a push endpoint
  is specified.
  """

  @staticmethod
  def Args(parser):
    _ArgsBeta(parser)
    _ArgsAlpha(parser)
