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
"""Flags and helpers for the App Topology CLI."""

from googlecloudsdk.calliope import arg_parsers


def AddDomainsFlag(parser, required=True):
  """Adds the --domains flag to the given argument parser.

  Args:
    parser: googlecloudsdk.calliope.parser_arguments.ArgumentInterceptor, The
      argument parser to register the flag with.
    required: bool, Whether the flag is required.
  """
  parser.add_argument(
      '--domains',
      type=arg_parsers.ArgList(),
      metavar='DOMAINS',
      required=required,
      help=(
          'List of App Topology domains to include in the topology query '
          '(e.g., SRE, DEVOPS, SECURITY).'
      ),
  )


def AddPatternGroup(parser):
  """Adds the mutually exclusive --pattern / --pattern-file argument group.

  Args:
    parser: googlecloudsdk.calliope.parser_arguments.ArgumentInterceptor, The
      argument parser to register the flag group with.
  """
  group = parser.add_group(
      mutex=True,
      required=False,
      help='Graph pattern filter options.',
  )
  group.add_argument(
      '--pattern',
      metavar='PATTERN',
      help=(
          'A GraphPattern query filter definition in proto3 YAML/JSON string '
          'format.'
      ),
  )
  group.add_argument(
      '--pattern-file',
      metavar='PATTERN_FILE',
      help=(
          'Path to a YAML or JSON file (or "-" for standard input) '
          'containing the GraphPattern query filter definition.'
      ),
  )
