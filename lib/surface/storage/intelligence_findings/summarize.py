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
"""Command to summarize intelligence findings."""

import argparse
import textwrap
from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Summarize(base.ListCommand):
  """Intelligence findings summary."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""
      Lists finding summaries for a specific container scope.
      """).strip(),
      'EXAMPLES': textwrap.dedent("""
      To summarize intelligence findings for project 'my-project':

          $ {command} --project=my-project
      """).strip(),
  }

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    scope_group = parser.add_mutually_exclusive_group(required=True)
    scope_group.add_argument(
        '--project', help='The project to scope the summary to.'
    )
    scope_group.add_argument(
        '--sub-folder', help='The sub-folder to scope the summary to.'
    )
    scope_group.add_argument(
        '--organization', help='The organization to scope the summary to.'
    )
    parser.add_argument(
        '--resource-scope', help='The resource scope for the summary.'
    )
    parser.add_argument(
        '--location', help='The location to scope the summary to.'
    )

  def Run(self, args: argparse.Namespace) -> None:
    del self  # Unused.
    raise NotImplementedError(
        'The intelligence-findings surface is not yet implemented.'
    )
