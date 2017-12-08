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

"""Command to describe named configuration."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.config import completers
from googlecloudsdk.core import named_configs
from googlecloudsdk.core import properties


class Describe(base.Command):
  """Describes a named configuration by listing its properties."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          See `gcloud topic configurations` for an overview of named
          configurations.
          """,
      'EXAMPLES': """\
          To describe existing named configuration, run:

            $ {command} my_config

          This is similar to:

            $ gcloud config configurations activate my_config

            $ gcloud config list
          """,
  }

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    configuration_arg = parser.add_argument(
        'configuration_name',
        help='Name of the configuration to describe')
    configuration_arg.completer = completers.NamedConfigCompleter
    parser.add_argument(
        '--all', action='store_true',
        help='Include unset properties in output.')

  def Run(self, args):
    fname = named_configs.GetPathForConfigName(args.configuration_name)

    if not named_configs.IsPathReadable(fname):
      raise named_configs.NamedConfigLoadError(
          'Reading named configuration [{0}] failed because [{1}] cannot '
          'be read.'.format(args.configuration_name, fname))

    return {
        'name': args.configuration_name,
        'is_active': (args.configuration_name ==
                      named_configs.GetNameOfActiveNamedConfig()),
        'properties': properties.VALUES.AllValues(
            list_unset=args.all,
            properties_file=properties.PropertiesFile([fname]),
            only_file_contents=True),
    }
