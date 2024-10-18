# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command that statically validates gcloud commands for corectness."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import copy
import json
import re
import shlex
from typing import collections

from googlecloudsdk import gcloud_main
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files
import six


_PARSING_OUTPUT_TEMPLATE = {
    'command_string': None,
    'success': False,
    'error_message': None,
    'error_type': None,
}


class CommandValidationError(Exception):
  pass


def _read_commands_from_file(commands_file):
  with files.FileReader(commands_file) as f:
    command_file_data = json.load(f)
  command_strings = []
  for command_data in command_file_data:
    command_strings.append(command_data['command_string'])
  return command_strings


def _separate_command_arguments(command_string: str):
  """Move all flag arguments to back."""
  # Split arguments
  command_arguments = shlex.split(command_string)
  # Move any flag arguments to end of command.
  flag_args = [arg for arg in command_arguments if arg.startswith('--')]
  command_args = [arg for arg in command_arguments if not arg.startswith('--')]
  return command_args + flag_args


def _add_equals_to_flags(command):
  """Adds equals signs to gcloud command flags, except for format and help flags."""

  pattern = (  # Matches flag name and its value (excluding format and help)
      r'(--[a-zA-Z0-9-]+) +([^-][^ ]*)'
  )
  replacement = r'\1=\2'  # Inserts equals sign between flag and
  modified_command = re.sub(pattern, replacement, command)
  # Remove = from flags without explicit values
  modified_command = re.sub(r'(--[a-zA-Z0-9-]+)= ', r'\1 ', modified_command)
  return modified_command


def _formalize_gcloud_command(command_str):
  command_str = _add_equals_to_flags(command_str)
  command_str = (
      command_str.replace('--project=PROJECT ', '--project=my-project ')
      .replace('--project=PROJECT_ID ', '--project=my-project ')
      .replace('$PROJECT_ID ', 'my-project ')
      .replace('YOUR_PROJECT_ID ', 'my-project ')
  )
  return command_str


def _extract_gcloud_commands(text):
  """Extracts code snippets from fenced code blocks within a text string.

  Args:
      text: The text string containing fenced code blocks.

  Returns:
      A list of extracted code snippets.
  """
  text = bytes(text, 'utf-8').decode('unicode_escape')
  # print(text)
  fenced_pattern = r'```(?:[\w ]+\n)?(.*?)```'
  indented_pattern = (  # 3-8 indented spaces as arbitray nums
      r'(?: {3-8}|\t)(.*?)(?:\n\S|\n$)'
  )
  combined_pattern = re.compile(
      f'{fenced_pattern}|{indented_pattern}', re.DOTALL
  )

  code_snippets = []
  for match in combined_pattern.finditer(
      text
  ):  # use finditer instead of findall
    command_str = match.group(1).strip()
    if 'gcloud ' not in command_str or not command_str.startswith('gcloud'):
      continue
    for cmd in command_str.split('gcloud '):
      cmd_new_lines = cmd.split('\n')
      if len(cmd_new_lines) >= 1 and cmd_new_lines[0].strip():
        command_str = _formalize_gcloud_command(cmd_new_lines[0].strip())
        code_snippets.append(f'gcloud {command_str}')
  return code_snippets


def _get_command_no_args(command_arguments):
  """Returns the command string without any arguments."""
  cli = gcloud_main.CreateCLI([])
  # Remove "gcloud" from command arguments.
  command_arguments = command_arguments[1:]
  current_command_node = cli._TopElement()  # pylint: disable=protected-access
  command_no_args = ['gcloud']
  for argument in command_arguments:
    # If this hits, we've found a command group with a flag passed.
    # e.g. gcloud compute --help
    if argument.startswith('--'):
      break
    # Attempt to load next section of command path.
    current_command_node = current_command_node.LoadSubElement(argument)
    # If not a valid section of command path, fail validation.
    if not current_command_node:
      break
    else:
      command_no_args.append(argument)
  return ' '.join(command_no_args)


@base.UniverseCompatible
class GenerateCommand(base.Command):
  """Generate YAML file to implement given command.

  The command YAML file is generated in the --output-dir directory.
  """

  _VALIDATION_RESULTS = []

  def _validate_command(self, command_string):
    """Validate a single command."""
    command_arguments = _separate_command_arguments(command_string)
    command_success, command_node, flag_arguments = (
        self._validate_command_prefix(command_arguments, command_string)
    )
    if not command_success:
      return
    flag_success = self._validate_command_suffix(
        command_node, flag_arguments, command_string
    )
    if not flag_success:
      return
    self._store_validation_results(True, command_string, flag_arguments)

  def _validate_commands_from_file(self, commands_file):
    """Validate multiple commands given in a file."""
    commands = _read_commands_from_file(commands_file)
    for command in commands:
      self._validate_command(command)

  def _validate_commands_from_text(self, commands_text_file):
    """Validate multiple commands given in a text string."""
    with files.FileReader(commands_text_file) as f:
      text = f.read()
    commands = _extract_gcloud_commands(text)
    for command in commands:
      self._validate_command(command)

  def _validate_command_prefix(self, command_arguments, command_string):
    """Validate that the argument string contains a valid command or group."""
    cli = gcloud_main.CreateCLI([])
    # Remove "gcloud" from command arguments.
    command_arguments = command_arguments[1:]
    index = 0
    current_command_node = cli._TopElement()  # pylint: disable=protected-access
    for argument in command_arguments:
      # If this hits, we've found a command group with a flag passed.
      # e.g. gcloud compute --help
      if argument.startswith('--'):
        return (
            True,
            current_command_node,
            command_arguments[index:],
        )
      # Attempt to load next section of command path.
      current_command_node = current_command_node.LoadSubElement(argument)
      # If not a valid section of command path, fail validation.
      if not current_command_node:
        self._store_validation_results(
            False,
            command_string,
            command_arguments[index:],
            "Invalid choice: '{}'".format(argument),
            'UnrecognizedCommandError',
        )
        return False, None, None
      index += 1
      # If command path is valid and is a command, return the command node.
      if not current_command_node.is_group:
        return (
            True,
            current_command_node,
            command_arguments[index:],
        )

    # If we make it here then only a command group has been provided.
    remaining_flags = command_arguments[index:]
    if not remaining_flags:
      self._store_validation_results(
          False,
          command_string,
          command_arguments[index:],
          'Command name argument expected',
          'UnrecognizedCommandError',
      )
      return False, None, None
    # If we've iterated through the entire list and end up here, something
    # unpredicted has happened.
    raise CommandValidationError(
        'Command could not be validated due to unforeseen edge case.'
    )

  def _validate_command_suffix(
      self, command_node, command_arguments, command_string
  ):
    """Validates that the given flags can be parsed by the argparse parser."""

    found_parent = False
    if command_arguments:
      for command_arg in command_arguments:
        if (
            '--project' in command_arg
            or '--folder' in command_arg
            or '--organization' in command_arg
        ):
          found_parent = True
    if not command_arguments:
      command_arguments = []
    if not found_parent:
      command_arguments.append('--project=myproject')
    try:
      command_node._parser.parse_args(command_arguments, raise_error=True)  # pylint: disable=protected-access
    except argparse.ArgumentError as e:
      self._store_validation_results(
          False,
          command_string,
          command_arguments,
          six.text_type(e),
          type(e).__name__,
      )
      return False
    return True

  def _store_validation_results(
      self,
      success,
      command_string,
      command_args=None,
      error_message=None,
      error_type=None,
  ):
    """Store information related to the command validation."""
    validation_output = copy.deepcopy(_PARSING_OUTPUT_TEMPLATE)
    validation_output['command_string'] = command_string
    validation_output['command_string_no_args'] = _get_command_no_args(
        _separate_command_arguments(command_string)
    )
    validation_output['command_args'] = sorted(command_args)
    validation_output['success'] = success
    validation_output['error_message'] = error_message
    validation_output['error_type'] = error_type
    self._VALIDATION_RESULTS.append(
        collections.OrderedDict(sorted(validation_output.items()))
    )

  def _log_validation_results(self):
    """Output collected validation results."""
    log.out.Print(json.dumps(self._VALIDATION_RESULTS))

  @staticmethod
  def Args(parser):
    command_group = parser.add_group(mutex=True)
    command_group.add_argument(
        '--command-string',
        help='Gcloud command to statically validate.',
    )
    command_group.add_argument(
        '--commands-file',
        help='JSON file containing list of gcloud commands to validate.',
    )
    command_group.add_argument(
        '--commands-text-file',
        help=(
            'Raw text containing gcloud command(s) to validate. For example,'
            ' the commands could be in fenced code blocks or indented code'
            ' blocks.'
        ),
    )

  def Run(self, args):
    if args.IsSpecified('command_string'):
      self._validate_command(args.command_string)
    elif args.IsSpecified('commands_text_file'):
      self._validate_commands_from_text(args.commands_text_file)
    else:
      self._validate_commands_from_file(args.commands_file)
    self._log_validation_results()
