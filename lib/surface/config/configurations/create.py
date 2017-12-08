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

"""Command to create named configuration."""

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.configurations import named_configs


class Create(base.SilentCommand):
  """Creates a new named configuration."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          See `gcloud topic configurations` for an overview of named
          configurations.
          """,
      'EXAMPLES': """\
          To create a new named configuration, run:

            $ {command} my_config
          """,
  }

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        'configuration_name',
        help='Name of the configuration to create')

  def Run(self, args):
    named_configs.ConfigurationStore.CreateConfig(args.configuration_name)

    log.CreatedResource(args.configuration_name)
    log.status.Print(
        'To use this configuration, activate it by running:\n'
        '  $ gcloud config configurations activate {name}'.format(
            name=args.configuration_name))
    return args.configuration_name
