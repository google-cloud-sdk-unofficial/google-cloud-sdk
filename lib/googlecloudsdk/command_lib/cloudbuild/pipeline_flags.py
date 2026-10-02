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

from googlecloudsdk.command_lib.cloudbuild import resource_args


def AddFileFlag(parser):
  """Add the --file flag."""
  parser.add_argument(
      '--file',
      default='./pipeline.yaml',
      help='Path to the pipeline definition file (YAML or JSON).',
  )


def AddServiceAccountFlag(parser):
  """Add the --service-account flag."""
  parser.add_argument(
      '--service-account',
      help=(
          'Orchestrator Service Account '
          '(e.g. projects/-/serviceAccounts/sa@... or sa@...).'
      ),
  )


def AddDisplayNameFlag(parser):
  """Add the --display-name flag."""
  parser.add_argument(
      '--display-name',
      help='Human-readable title for the pipeline.',
  )


def AddDryRunFlag(parser):
  """Add the --dry-run flag."""
  parser.add_argument(
      '--dry-run',
      action='store_true',
      default=False,
      help='Validate syntax and permissions without persisting changes.',
  )


def AddPipelineApplyFlags(parser):
  """Add all flags for the `gcloud builds pipelines apply` command."""
  # Supplies the PIPELINE positional along with --region, and resolves the ID
  # from `metadata.name` in the file named by --file when it is omitted.
  resource_args.AddPipelineResourceArg(parser, 'to apply')
  AddFileFlag(parser)
  AddServiceAccountFlag(parser)
  AddDisplayNameFlag(parser)
  AddDryRunFlag(parser)
