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
"""Flags and helpers for the dataflow command group."""

from googlecloudsdk.calliope import arg_parsers


def AddEnableTurnkeyAlertsFlag(parser):
  """Adds the --enable-turnkey-alerts flag to parser."""
  parser.add_argument(
      '--enable-turnkey-alerts',
      # TODO(b/416575089): Add a link to documentation once available.
      help='Enable Turnkey Alerts for this job. Disabled by default.',
      action=arg_parsers.StoreTrueFalseAction,
  )
