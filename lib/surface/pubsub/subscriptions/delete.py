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

import json
from apitools.base.py import exceptions as api_ex

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import text


class Delete(base.Command):
  """Deletes one or more Cloud Pub/Sub subscriptions."""

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""

    parser.add_argument('subscription', nargs='+',
                        help='One or more subscription names to delete.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A 2-tuple of lists, one populated with the subscription paths that were
      successfully deleted, the other one with the list of subscription paths
      that could not be deleted.
    """
    msgs = self.context['pubsub_msgs']
    pubsub = self.context['pubsub']

    succeeded = []
    failed = []

    for subscription_name in args.subscription:
      delete_req = msgs.PubsubProjectsSubscriptionsDeleteRequest(
          subscription=util.SubscriptionFormat(subscription_name))
      try:
        pubsub.projects_subscriptions.Delete(delete_req)
        succeeded.append(delete_req.subscription)
      except api_ex.HttpError as e:
        failed.append((delete_req.subscription,
                       json.loads(e.content)['error']['message']))

    return succeeded, failed

  def Display(self, args, result):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    succeeded, failed = result
    successes = len(succeeded)
    failures = len(failed)

    if successes:
      fmt = 'list[title="{0} {1} deleted successfully"]'.format(
          successes, text.Pluralize(successes, 'subscription'))
      resource_printer.Print([subscription for subscription in succeeded], fmt)

    if failures:
      fmt = 'list[title="{0} {1} failed"]'.format(
          failures, text.Pluralize(failures, 'subscription'))
      resource_printer.Print(
          ['{0} (reason: {1})'.format(subs, reason) for subs, reason in failed],
          fmt)
