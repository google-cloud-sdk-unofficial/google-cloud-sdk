# Copyright 2016 Google Inc. All Rights Reserved.
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
"""The gcloud bigtable emulator group."""

from googlecloudsdk.api_lib.emulators import bigtable_util
from googlecloudsdk.api_lib.emulators import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import platforms


class UnsupportedPlatformError(exceptions.Error):
  pass


class Bigtable(base.Group):
  """Manage your local bigtable emulator.

  This set of commands allows you to start and use a local bigtable emulator.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To start a local bigtable emulator, run:

            $ {command} start
          """,
  }

  # Override
  def Filter(self, context, args):
    current_os = platforms.OperatingSystem.Current()
    if current_os is platforms.OperatingSystem.WINDOWS:
      raise UnsupportedPlatformError(
          'The bigtable emulator is currently not supported on Windows.')

    util.EnsureComponentIsInstalled(bigtable_util.BIGTABLE,
                                    bigtable_util.BIGTABLE_TITLE)
