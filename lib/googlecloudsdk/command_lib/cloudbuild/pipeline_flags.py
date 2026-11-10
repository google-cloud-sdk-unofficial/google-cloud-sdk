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
"""Flags and helpers for Cloud Build Pipelines CLI commands."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import resource_args


def AddFileFlag(parser):
  """Add the --file flag."""
  parser.add_argument(
      '--file',
      default='./pipeline.yaml',
      help='Path to the pipeline definition file (YAML or JSON).',
  )


def AddDryRunFlag(parser):
  """Add the --dry-run flag."""
  parser.add_argument(
      '--dry-run',
      action='store_true',
      default=False,
      help='Validate syntax and permissions without persisting changes.',
  )


def AddParamsFlag(parser):
  """Add the --params flag."""
  parser.add_argument(
      '--params',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=(
          'Comma-separated key-value parameter overrides passed to the '
          'pipeline run (for example, `ENV=staging,IMAGE_TAG=v1.2.0`). These '
          'values override default parameter definitions in the pipeline '
          'configuration.'
      ),
  )


def AddStreamLogsFlag(parser):
  """Add the --stream-logs flag."""
  parser.add_argument(
      '--stream-logs',
      action='store_true',
      default=False,
      help=(
          'If set, stream raw container build logs from all active stages '
          'with `[<stage-id>]` prefixes instead of rendering the collapsible '
          'stage progress tree.'
      ),
  )


def AddPipelineApplyFlags(parser):
  """Add all flags for the `gcloud builds pipelines apply` command."""
  # Supplies the PIPELINE positional along with --region, and resolves the ID
  # from `name` in the file named by --file when it is omitted.
  resource_args.AddPipelineResourceArg(parser, 'to apply', from_file=True)
  AddFileFlag(parser)
  AddDryRunFlag(parser)


def AddPipelineRunFlags(parser):
  """Add all flags for the `gcloud builds pipelines run` command."""
  resource_args.AddPipelineResourceArg(parser, 'to run', from_file=False)
  AddParamsFlag(parser)
  execution_group = parser.add_group(mutex=True)
  base.ASYNC_FLAG.AddToParser(execution_group)
  AddStreamLogsFlag(execution_group)
