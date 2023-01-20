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
"""Gets IAM policy for a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.v1.get_iam_policy import command as command_v1
from googlecloudsdk.command_lib.functions.v2.get_iam_policy import command as command_v2


def _CommonArgs(parser):
  """Registers flags for this command."""
  flags.AddFunctionResourceArg(parser, 'to get IAM policy for')
  flags.AddGen2Flag(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class GetIamPolicy(base.ListCommand):
  """Get IAM policy for a Google Cloud Function."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To get the iam policy for `FUNCTION-1` run:

            $ {command} FUNCTION-1
          """,
  }

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    _CommonArgs(parser)

  def Run(self, args):
    """Runs the command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter.
    """
    if flags.ShouldUseGen2():
      return command_v2.Run(args, self.ReleaseTrack())
    else:
      return command_v1.Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class GetIamPolicyBeta(GetIamPolicy):
  """Gets IAM policy for a Google Cloud Function."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetIamPolicyAlpha(GetIamPolicyBeta):
  """Gets IAM policy for a Google Cloud Function."""
