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
"""Command to list intelligence finding revisions."""

import argparse
import textwrap
from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class List(base.ListCommand):
  """Historical revisions list of a finding."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""
      Lists all historical revisions of a specific finding in reverse chronological order.
      """).strip(),
      'EXAMPLES': textwrap.dedent("""
      To list revisions for finding '123':

          $ {command} --finding-id=123
      """).strip(),
  }

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--finding-id',
        required=True,
        help='The ID of the intelligence finding to list revisions for.',
    )
    parser.add_argument('--location', help='Location of the finding(s).')

  def Run(self, args: argparse.Namespace) -> None:
    del self  # Unused.
    raise NotImplementedError(
        'The intelligence-findings revisions surface is not yet implemented.'
    )
