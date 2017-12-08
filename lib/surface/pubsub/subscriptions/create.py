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
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.command_lib.util import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateBeta(base.CreateCommand):
  """Creates one or more Cloud Pub/Sub subscriptions.

  Creates one or more Cloud Pub/Sub subscriptions for a given topic.
  The new subscription defaults to a PULL subscription unless a push endpoint
  is specified.
  """

  @classmethod
  def Args(cls, parser):
    flags.AddSubscriptionResourceArg(parser, 'to create.', plural=True)
    flags.AddSubscriptionTopicResourceFlags(parser)
    flags.AddSubscriptionSettingsFlags(parser, cls.ReleaseTrack())
    labels_util.AddCreateLabelsFlags(parser)

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

    labels = labels_util.Diff.FromCreateArgs(args).Apply(
        client.messages.Subscription.LabelsValue)

    failed = []
    for subscription_name in args.subscription:
      subscription_ref = util.ParseSubscription(subscription_name)

      try:
        result = client.Create(subscription_ref, topic_ref, args.ack_deadline,
                               push_config, retain_acked_messages,
                               retention_duration, labels=labels)
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
