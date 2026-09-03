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
"""Command to list Firebase security rules releases or rulesets."""

from googlecloudsdk.api_lib.firebase import security_rules as rules_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


_DEFAULT_PAGE_LIMIT = 50
_RELEASES_FORMAT = (
    'table(name.basename():label=NAME, rulesetName.basename():label=RULESET,'
    ' updateTime:label=UPDATED)'
)
_RULESETS_FORMAT = (
    'table(name.basename():label=NAME, createTime:label=CREATED)'
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Firebase security rules releases or rulesets in a project."""

  detailed_help = {
      'EXAMPLES': """\
          To list all security rules releases in the current project:

            $ {command}

          To list all security rulesets in the current project:

            $ {command} --rulesets
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--rulesets',
        action='store_true',
        default=False,
        help='If specified, lists rulesets instead of releases.',
    )
    base.PAGE_SIZE_FLAG.SetDefault(parser, _DEFAULT_PAGE_LIMIT)
    base.LIMIT_FLAG.SetDefault(parser, _DEFAULT_PAGE_LIMIT)
    parser.display_info.AddFormat(_RELEASES_FORMAT)

  def Run(self, args):
    project_id = properties.VALUES.core.project.Get(required=True)
    client = rules_util.SecurityRulesClient()

    if args.rulesets:
      args.GetDisplayInfo().AddFormat(_RULESETS_FORMAT)
      return client.ListRulesets(
          project_id=project_id,
          page_size=args.page_size,
          limit=args.limit,
      )

    return client.ListReleases(
        project_id=project_id,
        page_size=args.page_size,
        limit=args.limit,
    )
