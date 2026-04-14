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
"""Command to list intelligence findings."""

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
  """Intelligence findings list."""
  _client_factory = intelligence_finding_api.IntelligenceFindingApi

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""
      Lists intelligence findings associated with a project.
      """).strip(),
      'EXAMPLES': textwrap.dedent("""
      To list intelligence findings:

          $ {command}
      """).strip(),
  }

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--location',
        default='global',
        help='Location of the finding(s).',
        hidden=True,
    )
    parser.display_info.AddUriFunc(lambda resource: resource.name)

  def Run(
      self, args: argparse.Namespace
  ) -> Iterator['storage_v2_messages.IntelligenceFinding']:
    return self._client_factory().list_findings(
        parent=f'projects/{properties.VALUES.core.project.GetOrFail()}/locations/{args.location}',
        page_size=args.page_size,
    )
