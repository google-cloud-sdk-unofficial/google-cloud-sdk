# Copyright 2018 Google Inc. All Rights Reserved.
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
"""`gcloud monitoring policies conditions create` command."""
from googlecloudsdk.api_lib.monitoring import policies
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import resource_args
from googlecloudsdk.command_lib.monitoring import util


class Create(base.CreateCommand):
  """Create a condition in an alerting policy."""

  @staticmethod
  def Args(parser):
    condition_arg = resource_args.CreateAlertPolicyResourceArg(
        'to add a condition to.')
    resource_args.AddResourceArgs(parser, [condition_arg])
    flags.AddMessageFlags(parser, 'condition')
    flags.AddConditionSettingsFlags(parser)

  def Run(self, args):
    client = policies.AlertPolicyClient()
    messages = client.messages

    policy_ref = args.CONCEPTS.name.Parse()
    condition = util.GetConditionFromArgs(args, messages)

    policy = client.Get(policy_ref)
    policy.conditions.append(condition)

    response = client.Update(policy_ref, policy)
    return response
