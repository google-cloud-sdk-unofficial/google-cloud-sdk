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

"""The gen-config command."""

import os

from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.app.ext_runtimes import fingerprinting
from googlecloudsdk.api_lib.app.runtimes import fingerprinter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


RUNTIME_MISMATCH_MSG = ("You've generated a Dockerfile that may be customized "
                        'for your application.  To use this Dockerfile, '
                        'please change the runtime field in [%s] to '
                        'custom.')


class GenConfig(base.Command):
  """Generate missing configuration files for a source directory.

  This command generates all relevant config files (app.yaml, Dockerfile and a
  build Dockerfile) for your application in the current directory or emits an
  error message if the source directory contents are not recognized.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To generate configs for the current directory:

            $ {command}

          To generate configs for ~/my_app:

            $ {command} ~/my_app
          """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'source_dir',
        nargs='?',
        help='The source directory to fingerprint.',
        default=os.getcwd())
    parser.add_argument(
        '--config',
        default=None,
        help=('The yaml file defining the module configuration.  This is '
              'normally one of the generated files, but when generating a '
              'custom runtime there can be an app.yaml containing parameters.'))
    parser.add_argument(
        '--custom',
        action='store_true',
        default=False,
        help=('If true, generate config files for a custom runtime.  This '
              'will produce a Dockerfile, a .dockerignore file and an app.yaml '
              '(possibly other files as well, depending on the runtime).'))

  def Run(self, args):
    if args.config:
      # If the user has specified an config file, use that.
      config_filename = args.config
    else:
      # Otherwise, check for an app.yaml in the source directory.
      config_filename = os.path.join(args.source_dir, 'app.yaml')
      if not os.path.exists(config_filename):
        config_filename = None

    # If there was an config file either specified by the user or in the source
    # directory, load it.
    if config_filename:
      try:
        myi = yaml_parsing.ModuleYamlInfo.FromFile(config_filename)
        config = myi.parsed
      except IOError as ex:
        log.error('Unable to open %s: %s', config_filename, ex)
        return
    else:
      config = None

    fingerprinter.GenerateConfigs(
        args.source_dir,
        fingerprinting.Params(appinfo=config, custom=args.custom))

    # If the user has a config file, make sure that they're using a custom
    # runtime.
    if config and args.custom and config.GetEffectiveRuntime() != 'custom':
      log.status.Print(RUNTIME_MISMATCH_MSG % config_filename)
