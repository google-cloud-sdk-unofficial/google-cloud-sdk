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

"""Defines arguments for BigLake commands."""

from googlecloudsdk.calliope import arg_parsers

# TODO(b/461544141): Move methods that define commands arguments from util.py
# to this file.


def AddPropertiesArg(parser):
  """Adds argument for creating properties."""
  parser.add_argument(
      '--properties',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=(
          'Properties associated with the namespace.'
      ),
  )


def AddUpdatePropertiesArgs(parser):
  """Adds arguments for updating properties."""
  parser.add_argument(
      '--update-properties',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=(
          'List of properties to update or add.'
      ),
  )
  parser.add_argument(
      '--remove-properties',
      metavar='KEY',
      type=arg_parsers.ArgList(),
      help=(
          'List of properties to remove.'
      ),
  )
  parser.add_argument(
      '--clear-properties',
      action='store_true',
      default=False,
      help=(
          'Clear all properties from the namespace.'
      ),
  )


def AddTableDescribeArgs(parser):
  """Adds arguments for describing tables."""
  parser.add_argument(
      '--snapshots',
      help='Snapshot to get.',
  )


def AddTableRegisterArgs(parser):
  """Adds arguments for registering tables."""
  parser.add_argument(
      '--metadata-location',
      required=True,
      help='Metadata location of the table.',
  )
  parser.add_argument(
      '--overwrite',
      action='store_true',
      default=False,
      help='Overwrite the table if it already exists.',
  )
