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
"""Cloud Pub/Sub subscriptions list command."""
from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import util


class List(base.ListCommand):
  """Lists Cloud Pub/Sub subscriptions.

  Lists all of the Cloud Pub/Sub subscriptions that exist in a given project.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
          table[box](
            projectId:label=PROJECT,
            subscriptionId:label=SUBSCRIPTION,
            topicId:label=TOPIC,
            type,
            ackDeadlineSeconds:label=ACK_DEADLINE
          )
        """)
    parser.display_info.AddUriFunc(util.SubscriptionUriFunc)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      Subscription paths that match the regular expression in args.name_filter.
    """
    client = subscriptions.SubscriptionsClient()
    for sub in client.List(util.ParseProject(), page_size=args.page_size):
      yield util.ListSubscriptionDisplayDict(sub)

