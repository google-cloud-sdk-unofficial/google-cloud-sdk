# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""The gcloud Firestore databases restore command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.firestore import databases
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Restore(base.Command):
  """Restores a Cloud Firestore database from a backup.

  ## EXAMPLES

  To restore a database from a backup.

      $ {command}
      --source-backup=projects/PROJECT_ID/locations/LOCATION_ID/backups/BACKUP_ID
      --destination-database=DATABASE_ID
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--source-backup',
        metavar='SOURCE_BACKUP',
        type=str,
        required=True,
        help=textwrap.dedent("""\
            The source backup to restore from.

            For example, to restore from backup `cf9f748a-7980-4703-b1a1-d1ffff591db0` in us-east1:

            $ {command} --source-backup=projects/PROJECT_ID/locations/us-east1/backups/cf9f748a-7980-4703-b1a1-d1ffff591db0
            """),
    )
    parser.add_argument(
        '--destination-database',
        metavar='DESTINATION_DATABASE',
        type=str,
        required=True,
        help=textwrap.dedent("""\
            Destination database to restore to. Destination database will be created in the same location as the source backup.

            For example, to restore to database `testdb`:

            $ {command} --destination-database=testdb
            """),
    )

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    return databases.RestoreDatabase(
        project, args.source_backup, args.destination_database
    )
