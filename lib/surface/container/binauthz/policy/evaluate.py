# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Evaluate policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import platform_policy
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags
from googlecloudsdk.core.exceptions import Error


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Evaluate(base.Command):
  """Evaluate a policy.

  ## EXAMPLES

  To evaluate a policy using its resource name:

    $ {command} projects/my_proj/platforms/gke/policies/policy1
    --resource=pod.json

  To evaluate the same policy using flags:

    $ {command} policy1 --platform=gke --project=my_proj --resource=pod.json
  """

  @staticmethod
  def Args(parser):
    flags.AddPlatformPolicyResourceArg(parser, 'to evaluate')
    flags.AddPodFileContentArg(parser)

  def Run(self, args):
    policy_ref = args.CONCEPTS.policy_resource_name.Parse().RelativeName()
    platform_id = policy_ref.split('/')[3]
    if platform_id != 'gke':
      raise Error(
          "Found unsupported platform '{}'. Currently only 'gke' platform "
          "policies are supported.".format(platform_id)
      )

    response = platform_policy.Client('v1').Evaluate(policy_ref, args.resource)

    # Set non-zero exit code for non-conformant verdicts to improve the
    # command's scriptability.
    if (
        response.verdict
        != apis.GetMessagesModule(
            'v1'
        ).EvaluateGkePolicyResponse.VerdictValueValuesEnum.CONFORMANT
    ):
      self.exit_code = 2

    return response
