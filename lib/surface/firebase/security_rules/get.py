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
"""Command to get a Firebase security rules release or ruleset."""

from googlecloudsdk.api_lib.firebase import security_rules as rules_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Get(base.DescribeCommand):
  """Get a Firebase security rules release or ruleset."""

  detailed_help = {
      'EXAMPLES': """\
          To get a security rules release named 'cloud.firestore/(default)':

            $ {command} cloud.firestore/(default)

          To get a security ruleset by ID:

            $ {command} RULESET_ID --ruleset
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'name',
        help=(
            'The name or ID of the release or ruleset to get (e.g.'
            ' cloud.firestore/(default), firebase.storage/BUCKET_NAME, or'
            ' RULESET_ID).'
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--ruleset',
        action='store_true',
        default=False,
        help='Get a ruleset with the given ID/name.',
    )
    group.add_argument(
        '--release',
        action='store_true',
        default=False,
        help='Get a release with the given name.',
    )

  def Run(self, args):
    project_id = properties.VALUES.core.project.Get(required=True)
    client = rules_util.SecurityRulesClient()

    if args.ruleset:
      return client.GetRuleset(project_id, args.name)

    return client.GetRelease(project_id, args.name)
