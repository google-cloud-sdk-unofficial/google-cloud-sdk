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
"""Command for spanner databases update."""

import textwrap

from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.spanner import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


# TODO(b/571177773): Drop `alpha` from the wait-for-reencryption
# references here and in NOTES once that command is promoted or replaced.
def _PrintReencryptionNotice(database_ref, args, asynchronous):
  """Prints guidance on waiting for background CMEK re-encryption."""
  if not (args.kms_keys or args.clear_kms_keys):
    return
  prefix = (
      'Encryption update request issued. '
      if asynchronous
      else 'Database encryption configuration updated. '
  )
  target_flag = (
      '--clear-kms-keys'
      if args.clear_kms_keys
      else '--kms-keys=' + ','.join(k.strip() for k in args.kms_keys)
  )
  log.status.Print(
      '{prefix}Existing data is re-encrypted in the background, which can take'
      ' several hours. To wait until re-encryption finishes, run:\n'
      '  $ gcloud alpha spanner databases wait-for-reencryption {db}'
      ' --instance={inst} --project={proj} {target_flag}\n'
      'Do not disable or destroy the previous KMS key(s) until re-encryption'
      ' finishes. Backups are not re-encrypted; keep the key(s) they were'
      ' created with until those backups are deleted or expire.'.format(
          prefix=prefix,
          db=database_ref.Name(),
          inst=database_ref.Parent().Name(),
          proj=database_ref.Parent().Parent().Name(),
          target_flag=target_flag,
      )
  )


@base.UniverseCompatible
class Update(base.UpdateCommand):
  """Update a Cloud Spanner database."""

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
        To enable database deletion protection on a Cloud Spanner database
        'my-database', run:

          $ {command} my-database --enable-drop-protection

        To disable database deletion protection on a Cloud Spanner database
        'my-database', run:

          $ {command} my-database --no-enable-drop-protection

        To update KMS key references for a Cloud Spanner database
        'my-database', run:

          $ {command} my-database --kms-keys="KEY1,KEY2"

        To remove all KMS key references and revert a Cloud Spanner database
        'my-database' to Google-managed encryption, run:

          $ {command} my-database --clear-kms-keys
        """),
      'NOTES': textwrap.dedent("""\
        When updating encryption with `--kms-keys` or `--clear-kms-keys`, the
        update operation completes after the new encryption configuration is
        recorded. Existing data is then re-encrypted in the background, which
        can take several hours. Do not disable or destroy the previous KMS
        key(s) until re-encryption finishes.

        Backups are not re-encrypted. Each backup keeps using the KMS key it
        was created with; keep that key until those backups are deleted or
        expire, or they can't be restored.

        To wait until background re-encryption finishes, run:

          $ gcloud alpha spanner databases wait-for-reencryption DATABASE --instance=INSTANCE (--kms-keys="KEY1,KEY2" | --clear-kms-keys)

        Or check progress manually with:

          $ gcloud spanner databases describe DATABASE --instance=INSTANCE --format="value(encryptionConfig,encryptionInfo)"

        and wait until `encryptionInfo` lists only the target encryption key(s)
        (or only `GOOGLE_DEFAULT_ENCRYPTION` for `--clear-kms-keys`). When
        transitioning from Google-managed encryption to CMEK, both checks
        report completion after the new key(s) are in use, which may be before
        all existing data has been re-encrypted.
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddDatabaseResourceArg(parser, 'to update')
    mutex_group = parser.add_argument_group(mutex=True)
    flags.EnableDropProtection().AddToParser(mutex_group)
    flags.EnableUpdateKmsKeys().AddToParser(mutex_group)
    flags.ClearKmsKeys().AddToParser(mutex_group)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs the `database update` command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Database update response.
    """
    database_ref = args.CONCEPTS.database.Parse()
    op = databases.Update(
        database_ref,
        enable_drop_protection=args.enable_drop_protection,
        kms_keys=args.kms_keys,
        clear_kms_keys=args.clear_kms_keys,
    )
    if args.async_:
      _PrintReencryptionNotice(database_ref, args, asynchronous=True)
      return op
    try:
      result = database_operations.Await(op, 'Updating database.')
    except (
        waiter.AbortWaitError,
        console_io.OperationCancelledError,
        waiter.TimeoutError,
        KeyboardInterrupt,
    ):
      # The Patch request has already been issued, so re-encryption
      # proceeds server-side even though we stopped waiting.
      _PrintReencryptionNotice(database_ref, args, asynchronous=True)
      raise
    _PrintReencryptionNotice(database_ref, args, asynchronous=False)
    return result
