# Copyright 2015 Google Inc. All Rights Reserved.
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
"""gcloud bigtable emulator env_init command."""

from googlecloudsdk.api_lib.emulators import bigtable_util
from googlecloudsdk.api_lib.emulators import util
from googlecloudsdk.calliope import base


class EnvInit(base.Command):
  """Print the commands required to export Bigtable emulator's env variables."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To print the env variables exports for a Bigtable emulator, run:

            $ {command}
          """,
  }

  def Run(self, args):
    data_dir = bigtable_util.GetDataDir()
    return util.ReadEnvYaml(data_dir)

  def Format(self, args):
    return 'config[export]'
