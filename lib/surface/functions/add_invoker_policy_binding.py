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
"""Add an invoker binding to the IAM policy of a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.v2.add_invoker_policy_binding import command
from googlecloudsdk.command_lib.iam import iam_util


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """\
          To add the invoker policy binding for `FUNCTION-1` from role
          `ROLE-1` for member `MEMBER-1` run:

            $ {command} FUNCTION-1 --member=MEMBER-1
          """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AddInvokerPolicyBinding(base.Command):
  """Adds an invoker binding to the IAM policy of a Google Cloud Function.

  This command applies to Cloud Functions 2nd gen only.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    flags.AddFunctionResourceArg(parser, 'to add the invoker binding to')
    iam_util.AddMemberFlag(parser, 'to add to the IAM policy', False)

  def Run(self, args):
    """Runs the command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated IAM policy for the service.
    """
    return command.Run(args, self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AddInvokerPolicyBindingBeta(AddInvokerPolicyBinding):
  """Adds an invoker binding to the IAM policy of a Google Cloud Function.

  This command applies to Cloud Functions 2nd gen only.
  """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddInvokerPolicyBindingAlpha(AddInvokerPolicyBindingBeta):
  """Add an invoker binding to the IAM policy of a Google Cloud Function.

  This command applies to Cloud Functions 2nd Gen only.
  """
