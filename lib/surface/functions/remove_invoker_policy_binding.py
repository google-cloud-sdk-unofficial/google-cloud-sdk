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
"""Remove an invoker binding from the IAM policy of a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.v2.remove_invoker_policy_binding import command
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveInvokerPolicyBinding(base.Command):
  """Remove an invoker binding from the IAM policy of a Google Cloud Function.

  This command applies to Cloud Functions V2 only.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddFunctionResourceArg(parser, 'to remove the invoker binding from')
    iam_util.AddMemberFlag(parser, 'to remove from the IAM policy', False)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated IAM policy for the service.
    """
    return command.Run(args, self.ReleaseTrack())
