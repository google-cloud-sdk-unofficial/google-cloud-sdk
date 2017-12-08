# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Cloud Pub/Sub subscriptions add-iam-policy-binding command."""
from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.command_lib.iam import base_classes
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import util


class AddIamPolicyBinding(base_classes.BaseIamCommand):
  """Add an IAM policy binding to a Cloud Pub/Sub Subscription."""

  detailed_help = iam_util.GetDetailedHelpForAddIamPolicyBinding(
      'subscription', 'my-subscription')

  @staticmethod
  def Args(parser):
    flags.AddSubscriptionResourceArg(parser,
                                     'to add an IAM policy binding to.')
    iam_util.AddArgsForAddIamPolicyBinding(parser)

  def Run(self, args):
    client = subscriptions.SubscriptionsClient()
    subscription_ref = util.ParseSubscription(args.subscription)
    return client.AddIamPolicyBinding(subscription_ref, args.member, args.role)

