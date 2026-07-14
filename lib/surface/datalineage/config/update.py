# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command to update Data Lineage configuration."""

import os

from apitools.base.py import encoding
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.datalineage import flags
from googlecloudsdk.command_lib.datalineage import util
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.DefaultUniverseOnly
class Update(base.Command):
  """Update Data Lineage configuration.

  ## EXAMPLES

  To update the configuration for the current project using a JSON file
  ``my_config.json``, run:

        $ {command} --config=my_config.json

  To update the configuration for the project ``my-project`` using an inline
  JSON string, run:

        $ {command} --project=my-project --config='{"ingestion": {"rules":
        [{"integrationSelector": {"integration": "BIGQUERY"},
        "lineageEnablement": {"enabled": true}}]}}'
  """

  @classmethod
  def Args(cls, parser):
    """Adds command-specific args."""
    flags.AddParentArgs(parser)
    parser.add_argument(
        '--config',
        required=True,
        help='Inline JSON/YAML config or path to a file containing it.',
    )

  def Run(self, args):
    """Runs the update command."""
    # 1. Load and Parse Config
    if os.path.exists(args.config):
      try:
        config_content = files.ReadFileContents(args.config)
      except files.Error as e:
        raise exceptions.BadFileException(
            'Could not read config file: {}'.format(e)
        ) from e
    else:
      config_content = args.config

    try:
      config_dict = yaml.load(config_content)
    except yaml.YAMLParseError as e:
      raise exceptions.InvalidArgumentException(
          '--config',
          'Must be a valid JSON/YAML string or a path to an existing file. '
          'Error parsing: {}'.format(e),
      ) from e

    if not config_dict:
      raise exceptions.InvalidArgumentException(
          '--config', 'Parsed config is empty.'
      )

    # 2. Resolve Service and Resource Name
    client = util.GetClient()
    messages = util.GetMessages()
    expected_name = util.GetConfigResourceName(args)

    # Validate/Override name in payload
    if 'name' in config_dict and config_dict['name'] != expected_name:
      raise exceptions.InvalidArgumentException(
          '--config',
          'Config name [{}] in payload does not match expected resource name'
          ' [{}] based on flags.'.format(config_dict['name'], expected_name),
      )
    config_dict['name'] = expected_name

    # 3. Convert Dict to Proto Message
    try:
      config_message = encoding.PyValueToMessage(
          messages.GoogleCloudDatacatalogLineageConfigmanagementV1Config,
          config_dict,
      )
    except Exception as e:
      raise exceptions.InvalidArgumentException(
          '--config',
          'Could not parse config into the expected schema. Error: {}'.format(
              e
          ),
      ) from e

    # 4. Call the correct service based on parent
    if args.folder:
      return client.folders_locations_config.Patch(config_message)
    elif args.organization:
      return client.organizations_locations_config.Patch(config_message)
    else:
      return client.projects_locations_config.Patch(config_message)
