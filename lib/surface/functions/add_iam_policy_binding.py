# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Add an IAM policy binding for a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.v1.add_iam_policy_binding import command as command_v1
from googlecloudsdk.command_lib.functions.v2.add_iam_policy_binding import command as command_v2
from googlecloudsdk.command_lib.iam import iam_util


def _CommonArgs(parser, track):
  """Registers flags for this command.

  Args:
    parser: The argparse parser.
    track: base.ReleaseTrack, calliope release track.
  """
  flags.AddFunctionResourceArg(parser, 'to add IAM policy binding for')
  iam_util.AddArgsForAddIamPolicyBinding(parser)

  flags.AddGen2Flag(parser, track)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AddIamPolicyBinding(base.Command):
  """Adds an IAM policy binding for a Google Cloud Function."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To add the iam policy binding for `FUNCTION-1` to role
          `ROLE-1` for member `MEMBER-1` run:

            $ {command} FUNCTION-1 --member=MEMBER-1 --role=ROLE-1
          """,
  }

  @staticmethod
  def Args(parser):
    """Registers flags for this command.

    Args:
      parser: The argparse parser.
    """
    _CommonArgs(parser, base.ReleaseTrack.GA)

  def Run(self, args):
    """Runs the command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated IAM policy.
    """
    if flags.ShouldUseGen2():
      return command_v2.Run(args, self.ReleaseTrack())
    else:
      return command_v1.Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AddIamPolicyBindingBeta(AddIamPolicyBinding):
  """Adds an IAM policy binding for a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Registers flags for this command.

    Args:
      parser: The argparse parser.
    """
    _CommonArgs(parser, base.ReleaseTrack.BETA)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddIamPolicyBindingAlpha(AddIamPolicyBindingBeta):
  """Adds an IAM policy binding for a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Registers flags for this command.

    Args:
      parser: The argparse parser.
    """
    _CommonArgs(parser, base.ReleaseTrack.ALPHA)
