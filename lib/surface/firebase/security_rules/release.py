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
"""Command to release Firebase security rules to a target release."""

import os
from googlecloudsdk.api_lib.firebase import security_rules as rules_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Release(base.Command):
  """Release security rules to a named Firebase release."""

  detailed_help = {
      'EXAMPLES': """\
          To release a rules file to Cloud Firestore default database:

            $ {command} cloud.firestore/(default) --source=firestore.rules

          To release an existing ruleset to Cloud Firestore default database:

            $ {command} cloud.firestore/(default) --ruleset=RULESET_ID

          To release a rules file to Cloud Storage default bucket:

            $ {command} firebase.storage/BUCKET_NAME --source=storage.rules
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'name',
        help=(
            'The name of the release (e.g. cloud.firestore/(default),'
            ' cloud.firestore/DATABASE_ID, firebase.storage/BUCKET_NAME).'
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--source',
        help='Path to a local rules file to deploy and release.',
    )
    group.add_argument(
        '--ruleset',
        help='The existing ruleset name or ID to release.',
    )

  def Run(self, args):
    project_id = properties.VALUES.core.project.Get(required=True)
    client = rules_util.SecurityRulesClient()

    ruleset_name = args.ruleset
    source_files = None
    if args.source:
      filename = os.path.basename(args.source)
      content = files.ReadFileContents(args.source)
      source_files = {filename: content}

    log.status.Print('Releasing security rules to [{}]...'.format(args.name))
    result = client.ReleaseRules(
        project_id=project_id,
        release_name=args.name,
        ruleset_name=ruleset_name,
        source_files=source_files,
    )
    log.status.Print('Successfully released rules to [{}]'.format(args.name))
    return result
