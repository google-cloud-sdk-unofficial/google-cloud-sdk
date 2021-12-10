# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

"""Remove IAM Policy Binding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.iap import util as iap_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveIamPolicyBinding(base.Command):
  """Remove IAM policy binding from an IAP gateway resource.

  Removes a policy binding from the IAM policy of an IAP gateway resource. One
  binding consists of a member, a role and an optional condition.
  """
  detailed_help = {
      'EXAMPLES':
          """\

          To remove an IAM policy binding for the role of 'roles/editor' for the
          user 'test-user@gmail.com', run:

            $ {command} --member='user:test-user@gmail.com' --role='roles/editor'

          To remove an IAM policy binding for the role of 'roles/editor' from
          all authenticated users,run:

            $ {command} --member='allAuthenticatedUsers' --role='roles/editor'

          To remove an IAM policy binding which expires at the end of the year
          2018 for the role of 'roles/browser' for the user 'test-user@gmail.com',
          run:

            $ {command} --member='user:test-user@gmail.com' --role='roles/browser'
                --condition='expression=request.time <
                timestamp("2019-01-01T00:00:00Z"),title=expires_end_of_2018,
                description=Expires at midnight on 2018-12-31'

          To remove all IAM policy bindings regardless of the condition for the
          role of 'roles/browser' and for the user 'test-user@gmail.com', run:

            $ {command} --member='user:test-user@gmail.com' --role='roles/browser'
            --all

          See https://cloud.google.com/iam/docs/managing-policies for details of
          policy role and member types.
  """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    iap_util.AddRemoveIamPolicyBindingArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter.
    """
    condition = iam_util.ValidateAndExtractCondition(args)
    iap_iam_ref = iap_util.ParseIapGatewayResource(self.ReleaseTrack())
    return iap_iam_ref.RemoveIamPolicyBinding(args.member, args.role, condition,
                                              args.all)
