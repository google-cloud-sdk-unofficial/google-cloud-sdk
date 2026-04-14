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
"""Command to describe an intelligence finding revision."""

import argparse
import textwrap
from googlecloudsdk.api_lib.storage import intelligence_finding_api
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.storage.v2 import storage_v2_messages


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Historical revision description of a finding."""
  _client_factory = intelligence_finding_api.IntelligenceFindingApi

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""
      Retrieves a specific historical revision of an intelligence finding.
      """).strip(),
      'EXAMPLES': textwrap.dedent("""
      To describe revision 'abc' for finding '123':

          $ {command} abc --finding-id=123
      """).strip(),
  }

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        'REVISION_ID',
        help='The ID of the revision to describe.',
    )
    parser.add_argument(
        '--finding-id',
        required=True,
        help='The ID of the intelligence finding the revision belongs to.',
    )
    parser.add_argument(
        '--location',
        default='global',
        help='Location of the finding(s).',
        hidden=True,
    )

  def Run(
      self, args: argparse.Namespace
  ) -> storage_v2_messages.IntelligenceFindingRevision:
    project = properties.VALUES.core.project.GetOrFail()
    revision_name = (
        f'projects/{project}/locations/{args.location}/intelligenceFindings/'
        f'{args.finding_id}/revisions/{args.REVISION_ID}'
    )
    return self._client_factory().get_revision(
        revision_name=revision_name
    )
