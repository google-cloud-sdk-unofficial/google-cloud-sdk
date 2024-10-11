# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Implementation of update command for updating management hub."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags


# TODO: b/369949089 - Remove default universe flag after checking the
# availability of management hub in different universes.
@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Updates Management Hub."""

  detailed_help = {
      'DESCRIPTION': """
          Update management hub plan for the organization, sub-folder
           or project.
      """,
      'EXAMPLES': """
          To limit buckets in the management hub plan, Use the following
          command with ``--include-bucket-ids'' and ``--include-bucket-regexes'' flags
          to specify list of bucket ids and bucket id regexes.,\n
            ${command} --organization=my-org --include-bucket-ids=my-bucket --include-bucket-regexes=my-bucket-.*

          To apply location based filters in the management hub plan, Use
          ``--include-locations'' or ``--exclude-locations'' flags to specify allowed
          list of locations or excluded list of locations. The following
          command updates management hub plan of sub-folder `123456` with the
          specified list of excluded locations.,\n
            ${command} --sub-folder=123456 --exclude-locations=us-east1,us-west1

          The following command updates management hub for the given project by
          inheriting existing management hub plan from the hierarchical parent
          resource.,\n
            ${command} --project=my-project --inherit-from-parent
      """,
  }

  @classmethod
  def Args(cls, parser):
    flags.add_management_hub_level_flags(parser)
    update_group = parser.add_group(category='UPDATE', mutex=True)
    update_group.add_argument(
        '--inherit-from-parent',
        action='store_true',
        help='Specifies management hub config to be inherited from parent.',
    )
    filters = update_group.add_group(category='FILTER')
    flags.add_management_hub_filter_flags(filters)

  def Run(self, args):
    # TODO: b/367267286 - Implementation of update command
    raise NotImplementedError
