# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""The gcloud run revisions group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Jobs(base.Group):
  """View and manage your Cloud Run jobs.

  This set of commands can be used to view and manage your Cloud Run jobs.
  """

  detailed_help = {
      'EXAMPLES': """
          To list your existing jobs, run:

            $ {command} list
      """,
  }

  @staticmethod
  def Args(parser):
    """Adds --region flag."""
    flags.AddRegionArg(parser)

  def Filter(self, context, args):
    """Runs before command.Run and validates platform with passed args."""
    self._CheckPlatform()
    return context

  def _CheckPlatform(self):
    platform = platforms.GetPlatform()
    if platform != platforms.PLATFORM_MANAGED:
      raise exceptions.PlatformError(
          'This command group is only supported for fully managed Cloud Run.')
