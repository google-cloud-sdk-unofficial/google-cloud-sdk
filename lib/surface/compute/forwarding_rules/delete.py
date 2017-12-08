# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Command for deleting forwarding rules."""

from googlecloudsdk.api_lib.compute import forwarding_rules_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import flags


class Delete(forwarding_rules_utils.ForwardingRulesMutator):
  """Delete forwarding rules.

  *{command}* deletes one or more Google Compute Engine forwarding rules.
  """

  FORWARDING_RULES_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FORWARDING_RULES_ARG = flags.ForwardingRuleArgumentPlural()
    cls.FORWARDING_RULES_ARG.AddArgument(parser)

  @property
  def method(self):
    return 'Delete'

  def CreateRequests(self, args):
    """Overrides."""
    forwarding_rule_refs = self.FORWARDING_RULES_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))

    utils.PromptForDeletion(forwarding_rule_refs)

    requests = []
    for forwarding_rule_ref in forwarding_rule_refs:
      self.global_request = getattr(forwarding_rule_ref, 'region', None) is None
      if self.global_request:
        request = self.messages.ComputeGlobalForwardingRulesDeleteRequest(
            forwardingRule=forwarding_rule_ref.Name(),
            project=self.project,)
      else:
        request = self.messages.ComputeForwardingRulesDeleteRequest(
            forwardingRule=forwarding_rule_ref.Name(),
            project=self.project,
            region=forwarding_rule_ref.region,)
      requests.append(request)

    return requests
