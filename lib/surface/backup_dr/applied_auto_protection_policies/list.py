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
"""List Backup and DR applied auto-protection policies."""

from googlecloudsdk.api_lib.backupdr import applied_auto_protection_policies
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.backupdr import flags

AppliedAutoProtectionPoliciesClient = (
    applied_auto_protection_policies.AppliedAutoProtectionPoliciesClient
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.Hidden
class List(base.ListCommand):
  """List Backup and DR applied auto-protection policies."""

  detailed_help = {
      'BRIEF': 'List Backup and DR applied auto-protection policies.',
      'DESCRIPTION': 'List Backup and DR applied auto-protection policies.',
      'EXAMPLES': """\
        To list applied auto-protection policies, run:

          $ {command} --location=us-central1
        """,
  }

  DEFAULT_LIST_FORMAT = """
      table(
        name.basename():label=ID,
        sourceBinding,
        status,
        createTime,
        updateTime
      )
  """

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
    """

    flags.AddOutputFormat(parser, List.DEFAULT_LIST_FORMAT)
    flags.AddLocationResourceArg(
        parser,
        'The location resource.',
        default='-',
    )
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    parent_ref = args.CONCEPTS.location.Parse()
    api_version = util.GetApiVersion(self.ReleaseTrack())
    client = AppliedAutoProtectionPoliciesClient(api_version=api_version)
    return client.List(
        parent_ref,
        limit=args.limit,
        page_size=args.page_size,
    )
