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
"""Cloud Pub/Sub subscription delete command."""
from apitools.base.py import exceptions as api_ex

from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import log


class Delete(base.DeleteCommand):
  """Deletes one or more Cloud Pub/Sub subscriptions."""

  @staticmethod
  def Args(parser):
    flags.AddSubscriptionResourceArg(parser, 'to delete.', plural=True)

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

    failed = []
    for subscription_name in args.subscription:
      subscription_ref = util.ParseSubscription(subscription_name)

      try:
        client.Delete(subscription_ref)
      except api_ex.HttpError as error:
        exc = exceptions.HttpException(error)
        log.DeletedResource(subscription_ref.RelativeName(),
                            kind='subscription',
                            failed=exc.payload.status_message)
        failed.append(subscription_name)
        continue

      subscription = client.messages.Subscription(
          name=subscription_ref.RelativeName())
      result = util.SubscriptionDisplayDict(subscription)
      log.DeletedResource(subscription_ref.RelativeName(), kind='subscription')
      yield result

    if failed:
      raise util.RequestsFailedError(failed, 'delete')
