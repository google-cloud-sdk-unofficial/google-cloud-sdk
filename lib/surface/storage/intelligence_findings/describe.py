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
from googlecloudsdk.api_lib.storage import intelligence_finding_api
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.storage.v2 import storage_v2_messages


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Intelligence finding description."""

  _client_factory: type[intelligence_finding_api.IntelligenceFindingApi] = (
      intelligence_finding_api.IntelligenceFindingApi
  )

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
    parser.add_argument(
        '--location',
        default='global',
        help='Location of the finding(s).',
        hidden=True,
    )

  def Run(
      self, args: argparse.Namespace
  ) -> storage_v2_messages.IntelligenceFinding:
    return self._client_factory().get_finding(
        name=f'projects/{properties.VALUES.core.project.GetOrFail()}/locations/{args.location}/intelligenceFindings/{args.FINDING_ID}'
    )
