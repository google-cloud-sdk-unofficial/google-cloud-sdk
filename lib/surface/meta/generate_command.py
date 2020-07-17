# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""A command that generates and/or updates help document directoriess."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os.path

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files


class GenerateCommand(base.Command):
  """Generate YAML file to implement given command.

  The command YAML file is generated in the --output-dir directory.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'command',
        metavar='COMMAND',
        help=('The full command to be auto-generated.'))
    parser.add_argument(
        '--output-dir',
        metavar='DIRECTORY',
        help=('The directory where the generated command YAML files '
              'will be written. If not specified then yaml files will '
              'not be generated. If no output directory is specified, '
              'the new YAML file will be written to stdout.'))

  def WriteYaml(self, full_command_path):
    command_yaml_data = 'boogleyboo'  # will eventually come from discovery doc
    with files.FileWriter(full_command_path, create_path=True) as f:
      f.write(command_yaml_data)
    log.status.Print('New file written at ' + full_command_path)

  def Run(self, args):
    command_filepath_list = args.command.replace('-', '_').split('.')
    command_filepath_list[-1] += '.yaml'
    command_filepath = os.path.join(*command_filepath_list)
    output_directory = args.output_dir
    full_command_path = os.path.join(output_directory, command_filepath)
    file_already_exists = os.path.exists(full_command_path)
    overwrite = False
    if file_already_exists:
      overwrite = console_io.PromptContinue(
          default=False,
          throw_if_unattended=True,
          message='This command already has a .yaml file, '
          'and continuing will overwrite the old file.')
    if not file_already_exists or overwrite:
      return self.WriteYaml(full_command_path)
    log.status.Print('No new file written at ' + full_command_path)
