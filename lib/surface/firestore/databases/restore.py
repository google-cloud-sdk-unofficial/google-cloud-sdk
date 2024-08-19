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
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class RestoreBeta(base.Command):
  """Restores a Cloud Firestore database from a backup.

  ## EXAMPLES

  To restore a database from a backup.

      $ {command}
      --source-backup=projects/PROJECT_ID/locations/LOCATION_ID/backups/BACKUP_ID
      --destination-database=DATABASE_ID
  """

  @classmethod
  def Args(cls, parser):
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

            This value should be 4-63 characters. Valid characters are /[a-z][0-9]-/
            with first character a letter and the last a letter or a number. Must
            not be UUID-like /[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/.

            Using "(default)" database ID is also allowed.

            For example, to restore to database `testdb`:

            $ {command} --destination-database=testdb
            """),
    )

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    return databases.RestoreDatabase(
        project,
        args.source_backup,
        args.destination_database,
        None,
        None,
    )


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RestoreAlpha(RestoreBeta):
  """Restores a Cloud Firestore database from a backup.

  ## EXAMPLES

  To restore a database from a backup.

      $ {command}
      --source-backup=projects/PROJECT_ID/locations/LOCATION_ID/backups/BACKUP_ID
      --destination-database=DATABASE_ID

  To restore to a CMEK-enabled database.

      $ {command}
      --source-backup=projects/PROJECT_ID/locations/LOCATION_ID/backups/BACKUP_ID
      --destination-database=DATABASE_ID
      --encryption-type=customer-managed-encryption
      --kms-key-name=projects/PROJECT_ID/locations/LOCATION_ID/keyRings/KEY_RING_ID/cryptoKeys/CRYPTO_KEY_ID
  """

  @classmethod
  def Args(cls, parser):
    super(RestoreAlpha, cls).Args(parser)
    encryption_config = parser.add_argument_group(
        required=False,
        help=textwrap.dedent("""\
            The encryption configuration of the restored database. If not specified, the same encryption settings as the backup will be used.

              To restore to a CMEK-enabled database:

                $ {command} --encryption-type=customer-managed-encryption --kms-key-name=projects/PROJECT_ID/locations/LOCATION_ID/keyRings/KEY_RING_ID/cryptoKeys/CRYPTO_KEY_ID

              To restore to a Google-default-encrypted database:

                $ {command} --encryption-type=google-default-encryption

              To restore to a database using the same encryption settings as the backup:

                $ {command} --encryption-type=backup-encryption
            """),
    )
    encryption_config.add_argument(
        '--encryption-type',
        metavar='ENCRYPTION_TYPE',
        type=str,
        required=True,
        choices=[
            'backup-encryption',
            'customer-managed-encryption',
            'google-default-encryption',
        ],
        help=textwrap.dedent("""\
            The encryption type of the destination database.
            """),
    )
    flags.AddKmsKeyNameFlag(
        encryption_config,
        'This flag must only be specified when encryption-type is'
        ' `customer-managed-encryption`.',
    )

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    return databases.RestoreDatabase(
        project,
        args.source_backup,
        args.destination_database,
        args.encryption_type,
        args.kms_key_name,
    )
