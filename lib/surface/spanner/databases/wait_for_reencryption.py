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
"""Command for spanner databases wait-for-reencryption."""

import re
import textwrap

from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.spanner import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

_KMS_KEY_NAME_RE = re.compile(
    r'^projects/[^/\s]+/locations/[^/\s]+/keyRings/[^/\s]+/cryptoKeys/[^/\s]+$'
)

_TIMEOUT_MESSAGE = (
    'Re-encryption has not yet converged after {duration}. The rotation is'
    ' still progressing server-side. Do NOT disable or destroy the previous KMS'
    ' key(s) yet. Check progress with:\n'
    '  gcloud spanner databases describe {database} --format=json\n'
    'and wait until encryptionInfo lists {target_description}. Databases with'
    ' little or no write traffic converge substantially more slowly.'
)

_OPERATION_ERROR_SUFFIX = (
    ' Do NOT disable or destroy any KMS key listed in encryptionInfo. Check'
    ' the current state with:\n'
    '  gcloud spanner databases describe {database} --format=json\n'
    'confirm encryptionConfig is the configuration you intend, then re-run'
    ' this command with matching --kms-keys/--clear-kms-keys.'
)

_TRANSIENT_ERROR_SUFFIX = (
    ' Do NOT disable or destroy the previous KMS key(s) yet. Check the'
    ' current state with:\n'
    '  gcloud spanner databases describe {database} --format=json\n'
    'and wait until encryptionInfo lists {target_description}.'
)

_CONFIG_MISMATCH_TIMEOUT_MESSAGE = (
    "Timed out after {duration} before the database's encryptionConfig"
    ' {actual_keys!r} matched the requested target {target_keys!r}. Either'
    ' an asynchronous update operation has not yet applied, or the'
    ' --kms-keys/--clear-kms-keys value does not match the database'
    ' configuration.'
    + _OPERATION_ERROR_SUFFIX
)

_ABORT_MESSAGE = (
    'Aborted waiting for database re-encryption to converge. The rotation'
    ' continues server-side. Do NOT disable or destroy the previous KMS key(s)'
    ' yet. Check progress with:\n'
    '  gcloud spanner databases describe {database} --format=json\n'
    'and wait until encryptionInfo lists {target_description}.'
)

_GMEK_CONVERGED_MESSAGE = (
    'Re-encryption has converged: encryptionInfo lists only'
    ' GOOGLE_DEFAULT_ENCRYPTION. The database no longer depends on the previous'
    ' KMS key(s). Existing backups keep using the key they were created with;'
    ' keep that key until those backups are deleted or expire.'
)

_CMEK_CONVERGED_MESSAGE = (
    'Re-encryption has converged at the KMS key level: encryptionInfo lists'
    ' only the target KMS key(s), and the database no longer depends on any'
    ' other KMS key. Older versions of the target key(s) listed in'
    ' encryptionInfo may still protect data; do not destroy those versions.'
    ' If the database previously used Google-managed encryption, some'
    ' pre-existing data may not yet be re-encrypted with the target key(s).'
    ' Existing backups keep using the key they were created with; keep that'
    ' key until those backups are deleted or expire.'
)


def _FormatDuration(max_wait_ms):
  """Formats a duration in milliseconds into a compact human-readable string."""
  if max_wait_ms % 3600000 == 0:
    return '{}h'.format(max_wait_ms // 3600000)
  if max_wait_ms % 60000 == 0:
    return '{}m'.format(max_wait_ms // 60000)
  if max_wait_ms % 1000 == 0:
    return '{}s'.format(max_wait_ms // 1000)
  return '{}ms'.format(max_wait_ms)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class WaitForReencryption(base.Command):
  """Wait for a Cloud Spanner database CMEK re-encryption to converge."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
        Wait for a Cloud Spanner database CMEK re-encryption transition to
        converge.

        Spanner CMEK transitions (`GMEK` to `CMEK`, `CMEK` to `CMEK`, and
        `CMEK` to `GMEK`) complete asynchronously in the background after the
        `UpdateDatabase` operation finishes. This command polls
        `databases.get` until `encryptionInfo` is non-empty and lists only the
        target `CUSTOMER_MANAGED_ENCRYPTION` KMS key(s) (`--kms-keys`) or only
        `GOOGLE_DEFAULT_ENCRYPTION` (`--clear-kms-keys`) across consecutive
        polls. Convergence is evaluated at the KMS key level (ignoring
        `/cryptoKeyVersions/<N>` suffixes), so older versions of the same KMS
        key may still wrap some data.

        This command can be run right after `gcloud spanner databases update
        --async`; it waits up to 10 minutes (measured on a monotonic clock,
        while `--timeout` uses wall-clock time) for the new configuration to
        apply before enforcing that `encryptionConfig` matches the requested
        target and has not diverged due to a concurrent update.

        When moving from Google-managed encryption to CMEK, `encryptionInfo`
        lists the new key(s) after they are in use. This indicates CMEK is
        active but may appear before all pre-existing data has been
        re-encrypted.

        Backups are not re-encrypted. Each backup keeps using the KMS key it
        was created with; keep that key until those backups are deleted or
        expire, or they can't be restored.

        To check convergence manually without this command, run:

          $ gcloud spanner databases describe DATABASE --instance=INSTANCE --format=json

        and verify that `encryptionInfo` is non-empty and lists only the target
        `CUSTOMER_MANAGED_ENCRYPTION` KMS key(s) (or only
        `GOOGLE_DEFAULT_ENCRYPTION` when reverting to Google-managed
        encryption).
        """),
      'EXAMPLES': textwrap.dedent("""\
        To wait for a Cloud Spanner database 'my-database' to finish
        re-encrypting to KMS keys, run:

          $ {command} my-database --instance=my-instance --kms-keys="projects/project1/locations/location1/keyRings/ring1/cryptoKeys/key1,projects/project1/locations/location2/keyRings/ring2/cryptoKeys/key2"

        To wait for a Cloud Spanner database 'my-database' to finish reverting
        to Google-managed encryption, run:

          $ {command} my-database --instance=my-instance --clear-kms-keys

        To wait with a custom timeout of 30 minutes, run:

          $ {command} my-database --instance=my-instance --kms-keys="projects/project1/locations/location1/keyRings/ring1/cryptoKeys/key1" --timeout=30m

        To start an asynchronous KMS key update and then wait for background
        re-encryption to converge, run:

          $ gcloud spanner databases update my-database --instance=my-instance --kms-keys="projects/project1/locations/location1/keyRings/ring1/cryptoKeys/key1,projects/project1/locations/location2/keyRings/ring2/cryptoKeys/key2" --async
          $ {command} my-database --instance=my-instance --kms-keys="projects/project1/locations/location1/keyRings/ring1/cryptoKeys/key1,projects/project1/locations/location2/keyRings/ring2/cryptoKeys/key2"
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddDatabaseResourceArg(parser, 'to wait for re-encryption')
    mutex_group = parser.add_argument_group(mutex=True, required=True)
    mutex_group.add_argument(
        '--kms-keys',
        type=arg_parsers.ArgList(min_length=1),
        metavar='KMS_KEY',
        action=arg_parsers.StoreOnceAction,
        help=(
            "Full set of KMS keys the database's encryption is expected to"
            ' converge to. Must match the keys passed to `gcloud spanner'
            ' databases update --kms-keys`.'
        ),
    )
    mutex_group.add_argument(
        '--clear-kms-keys',
        action='store_true',
        help='Wait for the database to converge to Google-managed encryption.',
    )
    parser.add_argument(
        '--timeout',
        type=arg_parsers.Duration(lower_bound='5m'),
        default='4h',
        help=(
            'Maximum time to wait for database CMEK re-encryption to converge.'
            ' See $ gcloud topic datetimes for information on duration formats.'
        ),
    )
    parser.display_info.AddFormat('yaml(name,encryptionConfig,encryptionInfo)')

  def Run(self, args):
    """Waits for the database's CMEK re-encryption to converge.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The converged Database message.
    """
    database_ref = args.CONCEPTS.database.Parse()
    if (
        properties.VALUES.regional.endpoint_mode.Get()
        == properties.constants.regional.REGIONAL
    ):
      raise exceptions.InvalidArgumentException(
          '--endpoint-mode',
          'Regional endpoints (--endpoint-mode=regional) are not supported'
          ' for this command because Spanner database resource names do not'
          ' include a location; use --endpoint-mode=global or'
          ' --endpoint-mode=regional-preferred.',
      )
    if args.clear_kms_keys:
      target_keys = set()
    else:
      target_keys = database_operations.GetDesiredEncryptionKeys(args.kms_keys)
      if not target_keys or any(
          not database_operations.GetDesiredEncryptionKeys([k])
          for k in args.kms_keys
      ):
        raise exceptions.InvalidArgumentException(
            '--kms-keys', 'Each KMS key resource name must be non-empty.'
        )
      invalid_keys = sorted(
          k for k in target_keys if not _KMS_KEY_NAME_RE.match(k)
      )
      if invalid_keys:
        raise exceptions.InvalidArgumentException(
            '--kms-keys',
            'Each value must be a fully qualified KMS key name'
            ' (projects/P/locations/L/keyRings/R/cryptoKeys/K): {}'.format(
                ', '.join(invalid_keys)
            ),
        )
    target_description = (
        'only GOOGLE_DEFAULT_ENCRYPTION'
        if args.clear_kms_keys
        else 'only the target KMS key(s)'
    )

    max_wait_ms = int(args.timeout * 1000)

    try:
      result = database_operations.AwaitReencryption(
          database_ref,
          target_keys=target_keys,
          max_wait_ms=max_wait_ms,
      )
    except waiter.TimeoutError as exc:
      if (
          isinstance(exc, database_operations.ReencryptionTimeoutError)
          and exc.config_mismatch_unresolved
      ):
        raise waiter.TimeoutError(
            _CONFIG_MISMATCH_TIMEOUT_MESSAGE.format(
                duration=_FormatDuration(max_wait_ms),
                actual_keys=sorted(exc.last_mismatched_config_keys or []),
                target_keys=sorted(target_keys),
                database=database_ref.RelativeName(),
            )
        ) from exc
      raise waiter.TimeoutError(
          _TIMEOUT_MESSAGE.format(
              duration=_FormatDuration(max_wait_ms),
              database=database_ref.RelativeName(),
              target_description=target_description,
          )
      ) from exc
    except (
        waiter.AbortWaitError,
        console_io.OperationCancelledError,
        KeyboardInterrupt,
    ) as exc:
      raise waiter.AbortWaitError(
          _ABORT_MESSAGE.format(
              database=database_ref.RelativeName(),
              target_description=target_description,
          )
      ) from exc
    except waiter.OperationError as exc:
      raise waiter.OperationError(
          '{}{}'.format(
              exc,
              _OPERATION_ERROR_SUFFIX.format(
                  database=database_ref.RelativeName(),
              ),
          )
      ) from exc
    except Exception as exc:  # pylint: disable=broad-except
      if database_operations.IsTransientError(exc):
        raise waiter.OperationError(
            'Transient errors polling database {database} for re-encryption'
            ' exceeded the maximum retry duration ({error}).{suffix}'.format(
                database=database_ref.RelativeName(),
                error=exc,
                suffix=_TRANSIENT_ERROR_SUFFIX.format(
                    database=database_ref.RelativeName(),
                    target_description=target_description,
                ),
            )
        ) from exc
      raise

    log.status.Print(
        _GMEK_CONVERGED_MESSAGE
        if args.clear_kms_keys
        else _CMEK_CONVERGED_MESSAGE
    )
    return result
