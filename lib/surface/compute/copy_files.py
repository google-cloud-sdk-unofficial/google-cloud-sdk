# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Implements the command for copying files from and to virtual machines."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scp_utils

DEPRECATION_WARNING = (
    '`gcloud compute copy-files` is deprecated.  Please use `gcloud compute '
    'scp` instead.  Note that `gcloud compute scp` does not have recursive '
    'copy on by default.  To turn on recursion, use the `--recurse` flag.')


@base.Deprecate(is_removed=False, warning=DEPRECATION_WARNING)
class CopyFiles(scp_utils.BaseScpCommand):
  """Copy files to and from Google Compute Engine virtual machines."""

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    super(CopyFiles, CopyFiles).Args(parser)

  def Run(self, args):
    """See scp_utils.BaseScpCommand.Run."""
    return super(CopyFiles, self).Run(args, recursive=True)
