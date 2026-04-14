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
from collections.abc import Iterator
import textwrap
from typing import TYPE_CHECKING

from googlecloudsdk.api_lib.storage import intelligence_finding_api
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
if TYPE_CHECKING:
  from googlecloudsdk.generated_clients.apis.storage.v2 import storage_v2_messages  # pylint: disable=g-import-not-at-top


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class List(base.ListCommand):
  """Historical revisions list of a finding."""
  _client_factory = intelligence_finding_api.IntelligenceFindingApi

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
    parser.add_argument(
        '--location',
        default='global',
        help='Location of the finding.',
        required=False,
        hidden=True,
    )
    parser.display_info.AddUriFunc(lambda resource: resource.name)

  def Run(
      self, args: argparse.Namespace
  ) -> Iterator['storage_v2_messages.IntelligenceFindingRevision']:
    project = properties.VALUES.core.project.GetOrFail()
    parent = f'projects/{project}/locations/{args.location}/intelligenceFindings/{args.finding_id}'
    return self._client_factory().list_revisions(
        parent=parent, page_size=args.page_size
    )
