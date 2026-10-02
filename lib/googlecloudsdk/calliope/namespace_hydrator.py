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

"""Calliope JSON argument hydration library."""

from googlecloudsdk.calliope import parser_extensions


def HydrateNamespace(calliope_command, payload):
  """Constructs and populates a Calliope Namespace from a Go payload.

  Args:
    calliope_command: calliope.backend.Command, The resolved Calliope command.
    payload: dict, The deserialized Go clap.Payload JSON dictionary:
      {
        'command_path': list[str],  # e.g. ['gcloud', 'compute', 'instances']
        'flags': [
          {
            'name': str,    # Flag name (e.g. 'zone' or '--zone')
            'value': any,   # Resolved flag value (including defaults from Go)
            'is_set': bool, # True if explicitly specified on the command line
          },
          ...
        ],
        'args': [
          {
            'name': str,    # Positional argument name (e.g. 'instance')
            'value': any,   # Resolved argument value
            'is_set': bool, # True if explicitly specified on the command line
          },
          ...
        ],
      }

  Returns:
    parser_extensions.Namespace, The populated Calliope namespace object.
  """
  # NOTE: To avoid loading parent commands or configuring/parsing ancestor args
  # in Python, gocloud (Go) should:
  # 1. Supply the target argparse `dest` attribute on each flag/arg item.
  # 2. Pass property overrides via standard `CLOUDSDK_<SECTION>_<PROPERTY>`
  #    environment variables (which `properties.VALUES` reads natively).
  parser = calliope_command._parser  # pylint: disable=protected-access
  parser._calliope_command = calliope_command  # pylint: disable=protected-access
  ns = parser_extensions.Namespace()
  ns._SetParser(parser)  # pylint: disable=protected-access

  for item in payload.get('flags') or []:
    name = item.get('name', '')
    val = item.get('value')
    is_set = item.get('is_set', False)

    dest = name.lstrip('-').replace('-', '_')
    setattr(ns, dest, val)
    if is_set:
      cli_name = name if name.startswith('-') else '--{}'.format(name)
      ns._specified_args[dest] = cli_name  # pylint: disable=protected-access

  for item in payload.get('args') or []:
    name = item.get('name', '')
    val = item.get('value')
    is_set = item.get('is_set', False)

    dest = name.replace('-', '_')
    setattr(ns, dest, val)
    if is_set:
      ns._specified_args[dest] = name  # pylint: disable=protected-access

  return ns
