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
"""Removes an invoker binding from the IAM policy of a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.v2.remove_invoker_policy_binding import command
from googlecloudsdk.command_lib.iam import iam_util


_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """\
          To remove the invoker policy binding for `FUNCTION-1` from role
          `ROLE-1` for member `MEMBER-1` run:

            $ {command} FUNCTION-1 --member=MEMBER-1
          """,
}


def _CommonArgs(parser, track):
  """Registers flags for this command."""
  del track
  flags.AddFunctionResourceArg(parser, 'to remove the invoker binding from')
  iam_util.AddMemberFlag(parser, 'to remove from the IAM policy', False)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class RemoveInvokerPolicyBinding(base.Command):
  """Removes an invoker binding from the IAM policy of a Google Cloud Function.

  This command applies to Cloud Functions V2 only.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    _CommonArgs(parser, base.ReleaseTrack.GA)

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
class RemoveInvokerPolicyBindingBeta(base.Command):
  """Removes an invoker binding from the IAM policy of a Google Cloud Function.

  This command applies to Cloud Functions V2 only.
  """
  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    _CommonArgs(parser, base.ReleaseTrack.BETA)

  def Run(self, args):
    """Runs the command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated IAM policy for the service.
    """
    return command.Run(args, self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveInvokerPolicyBindingAlpha(RemoveInvokerPolicyBindingBeta):
  """Removes an invoker binding from the IAM policy of a Google Cloud Function.

  This command applies to Cloud Functions V2 only.
  """

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    _CommonArgs(parser, base.ReleaseTrack.ALPHA)
