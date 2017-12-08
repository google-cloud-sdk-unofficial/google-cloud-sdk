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
"""gcloud datastore emulator env-unset command."""

from googlecloudsdk.api_lib.emulators import util
from googlecloudsdk.calliope import base


class EnvUnset(base.Command):
  """Print the commands required to unset a datastore emulators env variables.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To print the commands necessary to unset the env variables for
          a datastore emulator, run:

            $ {command} --data-dir DATA-DIR
          """,
  }

  def Run(self, args):
    return util.ReadEnvYaml(args.data_dir)

  def Format(self, args):
    return 'config[unset]'
