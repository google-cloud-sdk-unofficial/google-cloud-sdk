# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""'Bare Metal Solution snapshot schedule policies update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import exceptions
from googlecloudsdk.command_lib.bms import flags


DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a Bare Metal Solution snapshot schedule policy.
        """,
    'EXAMPLES':
        """
          To update an existing policy called ``my-policy'' with new description
          ``my-description'' and to replace any existing schedules with one
          that runs every 12 hours, run:

          $ {command} my-policy --description=my-description --schedule="crontab_spec=0 */12 * * *,retention_count=10,prefix=example"

    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Create a Bare Metal Solution snapshot schedule policy."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddSnapshotSchedulePolicyArgToParser(parser, positional=True)
    flags.AddSnapshotScheduleArgListToParser(parser, required=False)
    parser.add_argument('--description',
                        help='Textual description of the policy.')

  def Run(self, args):
    policy = args.CONCEPTS.snapshot_schedule_policy.Parse()
    description = args.description
    schedules = args.schedule
    if not description and not schedules:
      raise exceptions.NoConfigurationChangeError(
          'No configuration change was requested. Did you mean to include the '
          'flags `--description` or `--schedule`?')

    client = BmsClient()
    return client.UpdateSnapshotSchedulePolicy(policy_resource=policy,
                                               description=description,
                                               schedules=schedules)

Update.detailed_help = DETAILED_HELP
