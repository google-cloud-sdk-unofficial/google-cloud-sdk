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
"""Shared validation and Cloud Storage utilities for migration extractors."""

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.bq.migration import extractor_flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
import six

_QUERY_LOGS_SUFFIX = '-logs'
_QUERY_LOGS_EXACT = frozenset({'generic'})

CLOUD_ONLY_ARGS = (
    'zone',
    'secret',
    'gce_instance',
    'gce_startup_script_url',
    'gce_service_account',
    'service_account_user',
    'network',
    'subnet',
    'no_address',
)

_PUBLIC_IAM_MEMBERS = frozenset({'allUsers', 'allAuthenticatedUsers'})
_PUBLIC_ACCESS_PREVENTION_ENFORCED = 'enforced'


class BucketVerificationError(exceptions.Error):
  """Raised when output Cloud Storage bucket verification fails."""


def ValidateLocalModeFlags(args):
  """Rejects cloud-only flags when --run-mode=local.

  Args:
    args: argparse.Namespace, The parsed command-line arguments.

  Raises:
    calliope_exceptions.InvalidArgumentException: If any cloud-only flag is
      specified while --run-mode=local.
  """
  if args.run_mode != 'local':
    return
  for arg_name in CLOUD_ONLY_ARGS:
    if args.IsSpecified(arg_name):
      flag_name = '--{}'.format(arg_name.replace('_', '-'))
      raise calliope_exceptions.InvalidArgumentException(
          flag_name,
          'Cloud mode flags are only supported with --run-mode=cloud.',
      )


def _IsQueryLogsConnector(connector):
  """Returns True if the connector name is a query-logs connector."""
  normalized = (connector or '').strip().lower()
  return (
      normalized.endswith(_QUERY_LOGS_SUFFIX) or normalized in _QUERY_LOGS_EXACT
  )


def ValidateConnector(
    connector, extract_type=extractor_flags.ExtractType.METADATA
):
  """Validates that the connector matches the extraction subcommand type.

  Args:
    connector: str, The connector name passed via --connector.
    extract_type: extractor_flags.ExtractType, The extraction subcommand type.

  Raises:
    calliope_exceptions.InvalidArgumentException: If the connector is empty or
      belongs to a different extraction subcommand.
  """
  if not connector or not connector.strip():
    raise calliope_exceptions.InvalidArgumentException(
        '--connector', 'Connector name cannot be empty.'
    )

  is_logs = _IsQueryLogsConnector(connector)
  if extract_type == extractor_flags.ExtractType.METADATA and is_logs:
    raise calliope_exceptions.InvalidArgumentException(
        '--connector',
        "Connector '{}' is a query-logs connector. Use 'gcloud alpha bq"
        " migration query-logs extract' or specify a metadata connector"
        ' (without the -logs suffix).'.format(connector),
    )
  if extract_type == extractor_flags.ExtractType.QUERY_LOGS and not is_logs:
    raise calliope_exceptions.InvalidArgumentException(
        '--connector',
        "Connector '{}' is a metadata connector. Use 'gcloud alpha bq"
        " migration metadata extract' or specify a query-logs connector"
        ' (ending with -logs, or generic).'.format(connector),
    )


def IsGcsOutputUri(output_uri):
  """Returns True if output_uri has the gs:// Cloud Storage prefix."""
  return bool(
      output_uri and output_uri.startswith(storage_util.GSUTIL_BUCKET_PREFIX)
  )


def ValidateLocalOutputPath(output_path, expected_owner=None):
  """Validates a local filesystem output path for --run-mode=local.

  Args:
    output_path: str, The target local file or directory path.
    expected_owner: str or None, Value of --expected-owner (rejected when
      --output is a local path).

  Raises:
    calliope_exceptions.InvalidArgumentException: If output_path is empty, uses
      a non-gs:// URI scheme, or is combined with --expected-owner.
  """
  if not output_path or not output_path.strip():
    raise calliope_exceptions.InvalidArgumentException(
        '--output', 'Output path cannot be empty.'
    )
  if '://' in output_path:
    raise calliope_exceptions.InvalidArgumentException(
        '--output',
        "Output '{}' is not a valid local path or Cloud Storage URI (expected a"
        ' local file path or gs://bucket/path).'.format(output_path),
    )
  if expected_owner is not None:
    raise calliope_exceptions.InvalidArgumentException(
        '--expected-owner',
        '--expected-owner can only be used when --output is a Cloud Storage URI'
        ' (gs://bucket/path).',
    )


def ParseGcsOutputUri(output_uri):
  """Parses and validates a gs:// output URI.

  Args:
    output_uri: str, The target Cloud Storage URI (gs://bucket[/path]).

  Returns:
    storage_util.ObjectReference, The parsed bucket and object prefix.

  Raises:
    calliope_exceptions.InvalidArgumentException: If output_uri is not a valid
      gs:// URI.
  """
  if not output_uri or not output_uri.startswith(
      storage_util.GSUTIL_BUCKET_PREFIX
  ):
    raise calliope_exceptions.InvalidArgumentException(
        '--output',
        "Output '{}' is not a valid Cloud Storage path (expected"
        ' gs://bucket/path).'.format(output_uri),
    )
  try:
    obj_ref = storage_util.ObjectReference.FromUrl(
        output_uri, allow_empty_object=True
    )
    storage_util.ValidateBucketUrl(obj_ref.bucket)
  except (ValueError, storage_util.InvalidNameError) as err:
    raise calliope_exceptions.InvalidArgumentException(
        '--output', six.text_type(err)
    ) from err
  return obj_ref


def VerifyOutputBucket(output_uri, expected_owner=None, storage_client=None):
  """Verifies that the output GCS bucket is owned by expected_owner and private.

  To prevent bucket squatting and accidental exposure of extracted warehouse
  schemas or query logs (b/463466015, b/448885424), this function verifies that:
  1. The target bucket belongs to `expected_owner` (or the active `core/project`
     property if `expected_owner` is not specified) via `buckets.List`.
  2. The bucket does not grant public access (`allUsers` or
     `allAuthenticatedUsers`). If `iamConfiguration.publicAccessPrevention` is
     `'enforced'` on the bucket metadata returned by `buckets.List`, Cloud
     Storage blocks public access at the platform level and `GetIamPolicy`
     (which requires `storage.buckets.getIamPolicy` / `roles/storage.admin`) is
     skipped. Otherwise, `GetIamPolicy` is called to inspect the bucket's IAM
     bindings.

  Args:
    output_uri: str, The target Cloud Storage URI (gs://bucket[/path]).
    expected_owner: str or None, Expected owner project ID. Defaults to the
      active core/project property.
    storage_client: storage_api.StorageClient or None, Optional client override
      for testing.

  Returns:
    storage_util.ObjectReference, The parsed output reference.

  Raises:
    calliope_exceptions.InvalidArgumentException: If output_uri is malformed.
    properties.RequiredPropertyError: If expected_owner is not specified and
      no default core/project property is configured.
    BucketVerificationError: If the bucket is not owned by expected_owner or
      grants public access to allUsers / allAuthenticatedUsers.
  """
  obj_ref = ParseGcsOutputUri(output_uri)
  bucket_name = obj_ref.bucket
  owner_project = expected_owner or properties.VALUES.core.project.Get(
      required=True
  )
  client = storage_client or storage_api.StorageClient()

  log.status.Print('Verifying bucket gs://{}...'.format(bucket_name))

  list_req = client.messages.StorageBucketsListRequest(
      project=owner_project,
      prefix=bucket_name,
  )
  try:
    matched_bucket = next(
        (
            b
            for b in list_pager.YieldFromList(
                client.client.buckets, list_req, batch_size=None
            )
            if b.id == bucket_name or b.name == bucket_name
        ),
        None,
    )
  except apitools_exceptions.HttpError as err:
    raise BucketVerificationError(
        'Bucket gs://{} is not owned by project {} (or you do not have'
        ' permission to list buckets in that project): {}'.format(
            bucket_name, owner_project, err
        )
    ) from err

  if matched_bucket is None:
    raise BucketVerificationError(
        'Bucket gs://{} is not owned by project {} (or you do not have'
        ' permission to list buckets in that project).'.format(
            bucket_name, owner_project
        )
    )

  if (
      matched_bucket.iamConfiguration
      and matched_bucket.iamConfiguration.publicAccessPrevention
      == _PUBLIC_ACCESS_PREVENTION_ENFORCED
  ):
    return obj_ref

  try:
    policy = client.GetIamPolicy(obj_ref.bucket_ref)
  except apitools_exceptions.HttpError as err:
    raise BucketVerificationError(
        'Failed to inspect IAM policy for bucket gs://{} (Public Access'
        ' Prevention is not enforced on the bucket, and you do not have'
        ' storage.buckets.getIamPolicy permission; either enforce Public Access'
        ' Prevention on the bucket or grant roles/storage.admin): {}'.format(
            bucket_name, err
        )
    ) from err

  for binding in policy.bindings or []:
    if any(member in _PUBLIC_IAM_MEMBERS for member in binding.members or []):
      raise BucketVerificationError(
          'Bucket gs://{} has public access (allUsers or'
          ' allAuthenticatedUsers).'.format(bucket_name)
      )

  return obj_ref


def CleanDumperArgs(dumper_args):
  """Returns forwarded dumper arguments with any leading '--' separator removed.

  Args:
    dumper_args: list[str] or None, Positional remainder arguments.

  Returns:
    list[str], Cleaned list of arguments to forward to the dumper.
  """
  if not dumper_args:
    return []
  cleaned = list(dumper_args)
  if cleaned and cleaned[0] == '--':
    cleaned = cleaned[1:]
  return cleaned
