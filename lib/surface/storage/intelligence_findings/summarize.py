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
from collections.abc import Iterator
import textwrap
from googlecloudsdk.api_lib.storage import intelligence_finding_api
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.storage.v2 import storage_v2_messages


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Summarize(base.ListCommand):
  """Intelligence findings summary."""
  _client_factory: type[intelligence_finding_api.IntelligenceFindingApi] = (
      intelligence_finding_api.IntelligenceFindingApi
  )

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
    scope_group = parser.add_mutually_exclusive_group()
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
        '--resource-scope',
        type=str.upper,
        choices=['PROJECT', 'PARENT'],
        help=(
            'The resource scope for the summary. If not specified, summaries'
            ' are aggregated at the level of the parent resource.'
        ),
    )
    parser.add_argument(
        '--location',
        default='global',
        help='The location to scope the summary to.',
        hidden=True,
    )
    parser.display_info.AddUriFunc(lambda resource: resource.targetResource)

  def Run(
      self, args: argparse.Namespace
  ) -> Iterator[storage_v2_messages.FindingSummary]:
    location = args.location
    if args.organization:
      parent = f'organizations/{args.organization}/locations/{location}'
    elif args.sub_folder:
      parent = f'folders/{args.sub_folder}/locations/{location}'
    else:
      project = (
          args.project
          if args.project
          else properties.VALUES.core.project.GetOrFail()
      )
      parent = f'projects/{project}/locations/{location}'

    return self._client_factory().summarize_findings(
        parent=parent,
        resource_scope=args.resource_scope,
        page_size=args.page_size,
    )
