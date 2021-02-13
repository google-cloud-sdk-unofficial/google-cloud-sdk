# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Enable-enforce command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.orgpolicy import service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import interfaces


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EnableEnforce(interfaces.OrgPolicyGetAndUpdateCommand):
  r"""Enable enforcement of a boolean constraint.

  Enables enforcement of a boolean constraint. The policy will be created if it
  does not exist. Cannot be used with conditional policies.

  ## EXAMPLES

  To enable enforcement of the constraint 'iam.disableServiceAccountCreation' on
  the Project 'foo-project', run:

    $ {command} iam.disableServiceAccountCreation --project=foo-project
  """

  @staticmethod
  def Args(parser):
    super(EnableEnforce, EnableEnforce).Args(parser)

  def UpdatePolicy(self, policy, args):
    """Enables enforcement by removing old rules and creating a new rule with enforce set to True.

    Args:
      policy: messages.GoogleCloudOrgpolicyV2alpha1Policy, The policy to be
        updated.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
      The updated policy.
    """
    messages = service.OrgPolicyMessages(self.ReleaseTrack())
    new_rule = messages.GoogleCloudOrgpolicyV2alpha1PolicySpecPolicyRule()
    new_rule.enforce = True

    new_policy = copy.deepcopy(policy)
    new_policy.spec.rules = [new_rule]

    return new_policy
