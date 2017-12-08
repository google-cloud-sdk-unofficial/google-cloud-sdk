# Copyright 2013 Google Inc. All Rights Reserved.
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

"""A command that prints out information about your gcloud environment."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib import info_holder
from googlecloudsdk.core import log
from googlecloudsdk.core.util import platforms


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Info(base.Command):
  """Display information about the current gcloud environment.

     This command displays information about the current gcloud environment.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--show-log',
        action='store_true',
        help='Print the contents of the last log file.')

  def Run(self, args):
    holder = info_holder.InfoHolder()
    python_version = platforms.PythonVersion()
    if not python_version.IsSupported():
      log.warn(('Only Python version {0} is supported for the Cloud SDK. Many '
                'commands will work with a previous version, but not all.'
               ).format(python_version.MinSupportedVersionString()))
    return holder

  def Display(self, args, info):
    log.Print(info)

    if args.show_log and info.logs.last_log:
      log.Print('\nContents of log file: [{0}]\n'
                '==========================================================\n'
                '{1}\n\n'
                .format(info.logs.last_log, info.logs.LastLogContents()))

