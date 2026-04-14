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
"""Command to describe an intelligence finding."""

import argparse
import textwrap
from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Intelligence finding description."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""
      Retrieves detailed information about a specific intelligence finding by its ID.
      """).strip(),
      'EXAMPLES': textwrap.dedent("""
      To describe intelligence finding with ID '123':

          $ {command} 123
      """).strip(),
  }

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        'FINDING_ID',
        help='The ID of the intelligence finding to describe.',
    )
    parser.add_argument('--location', help='Location of the finding(s).')

  def Run(self, args: argparse.Namespace) -> None:
    del self  # Unused.
    raise NotImplementedError(
        'The intelligence-findings surface is not yet implemented.'
    )
