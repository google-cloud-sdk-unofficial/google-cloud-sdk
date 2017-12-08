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
"""gcloud datastore emulator env-init command."""

from googlecloudsdk.api_lib.emulators import util
from googlecloudsdk.calliope import base


class EnvInit(base.Command):
  """Print the commands required to export env variables of a datastore.

  Prints the commands but does not execute them. It will output
  in shell syntax or on Windows it will be in cmd.exe syntax.

  ## EXAMPLES

  To print the env variables exports for a datastore emulator, run:

    $ {command} --data-dir DATA-DIR
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
  }

  def Run(self, args):
    return util.ReadEnvYaml(args.data_dir)

  def Format(self, args):
    return 'config[export]'
