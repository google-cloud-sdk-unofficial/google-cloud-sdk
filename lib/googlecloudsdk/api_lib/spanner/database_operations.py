# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Spanner database operations API helper."""

from collections import abc
import re
import time

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from google.auth import exceptions as google_auth_exceptions
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
import requests

NOT_CONVERGED = object()
TRANSIENT = object()

# Database.encryptionInfo only changes when Spanner records a new key version
# or stops using an old one, so it is effectively monotonic; the extra poll
# guards against one stale read.
DEFAULT_CONSECUTIVE_POLLS = 2
DEFAULT_CONSECUTIVE_DIVERGENT_POLLS = 2
DEFAULT_CONFIG_APPLY_GRACE_MS = 10 * 60 * 1000  # 10 minutes
DEFAULT_MAX_TRANSIENT_ERROR_DURATION_MS = 30 * 60 * 1000  # 30 minutes
REENCRYPTION_MAX_WAIT_MS = 4 * 60 * 60 * 1000  # 4 hours
REENCRYPTION_SLEEP_MS = 10000  # 10 seconds
REENCRYPTION_WAIT_CEILING_MS = 30000  # 30 seconds
_EXPONENTIAL_SLEEP_MULTIPLIER = 1.4
_JITTER_MS = 1000

_TRANSIENT_HTTP_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
_TRANSIENT_ERROR_WARNING_THRESHOLD = 5

_CRYPTO_KEY_VERSION_RE = re.compile(r'/cryptoKeyVersions/[^/]+$')
_PROJECT_SEGMENT_RE = re.compile(r'^projects/([^/]+)/')


class Error(exceptions.Error):
  """Exceptions for the Spanner database_operations module."""


class ReencryptionArgumentError(Error):
  """Raised when an invalid argument is passed to re-encryption helpers."""


class ReencryptionConfigDivergedError(Error, waiter.OperationError):
  """Raised when database encryptionConfig diverges from the requested target."""


class ReencryptionTargetMismatchError(Error, waiter.OperationError):
  """Raised when database encryptionConfig does not match target within grace."""


class ReencryptionTimeoutError(Error, waiter.TimeoutError):
  """Raised when re-encryption does not converge within max_wait_ms.

  Attributes:
    config_mismatch_unresolved: True if Database.encryptionConfig was observed
      not matching the target and never matched before the timeout.
    last_mismatched_config_keys: The encryptionConfig key set from the most
      recent mismatch before any match, or None if config_mismatch_unresolved is
      False.
  """

  def __init__(
      self,
      message,
      config_mismatch_unresolved=False,
      last_mismatched_config_keys=None,
  ):
    super().__init__(message)
    self.config_mismatch_unresolved = config_mismatch_unresolved
    self.last_mismatched_config_keys = last_mismatched_config_keys


def _StripCryptoKeyVersion(kms_key_version):
  """Strips surrounding whitespace and trailing '/cryptoKeyVersions/<N>'."""
  if not kms_key_version:
    return ''
  return _CRYPTO_KEY_VERSION_RE.sub('', kms_key_version.strip()).strip()


def _StripProjectPrefix(key_name):
  """Strips the leading 'projects/<project>/' segment from a KMS key name."""
  return _PROJECT_SEGMENT_RE.sub('', key_name)


def _HasProjectNumber(key_name):
  """Returns True if the KMS key name's project segment is a project number."""
  match = _PROJECT_SEGMENT_RE.match(key_name)
  if not match:
    return False
  # GCP project IDs must start with a letter, so an all-digit segment is a
  # project number.
  return match.group(1).isdigit()


def GetConvergedEncryptionKeys(database):
  """Evaluates key-level encryption convergence from a Database message.

  Args:
    database: spanner_v1_messages.Database message.

  Returns:
    A set of KMS key resource names (with trailing /cryptoKeyVersions/<N>
    stripped) when every encryptionInfo entry is CUSTOMER_MANAGED_ENCRYPTION,
    an empty set when every encryptionInfo entry is GOOGLE_DEFAULT_ENCRYPTION,
    or NOT_CONVERGED otherwise (including when encryptionInfo is empty/absent,
    contains a mix of types, or contains any unrecognised encryptionType).
  """
  if database is None or not database.encryptionInfo:
    return NOT_CONVERGED

  types = {
      entry.encryptionType.name if entry.encryptionType else None
      for entry in database.encryptionInfo
  }
  if types == {'GOOGLE_DEFAULT_ENCRYPTION'}:
    return set()

  if types == {'CUSTOMER_MANAGED_ENCRYPTION'}:
    keys = set()
    for entry in database.encryptionInfo:
      key_name = _StripCryptoKeyVersion(entry.kmsKeyVersion)
      if not key_name:
        return NOT_CONVERGED
      keys.add(key_name)
    return keys

  return NOT_CONVERGED


def GetDesiredEncryptionKeys(kms_keys):
  """Normalizes an iterable of KMS key names into a set of stripped key names.

  Args:
    kms_keys: Iterable of KMS key resource name strings, or None for
      Google-managed encryption.

  Returns:
    set[str]: The set of desired KMS key names with trailing
      '/cryptoKeyVersions/<N>' stripped (empty set for GMEK).

  Raises:
    ReencryptionArgumentError: If kms_keys is a string, mapping, or
      non-iterable, or contains non-string elements.
  """
  if kms_keys is None:
    return set()
  if isinstance(kms_keys, (str, bytes, abc.Mapping)) or not isinstance(
      kms_keys, abc.Iterable
  ):
    raise ReencryptionArgumentError(
        'kms_keys must be an iterable of key-name strings or None.'
    )
  keys = set()
  for k in kms_keys:
    if not isinstance(k, str):
      raise ReencryptionArgumentError(
          'Expected key-name string in kms_keys, got {!r}.'.format(
              type(k).__name__
          )
      )
    stripped = _StripCryptoKeyVersion(k)
    if stripped:
      keys.add(stripped)
  return keys


def GetEncryptionConfigKeys(encryption_config):
  """Extracts the set of KMS key names from an EncryptionConfig message.

  Args:
    encryption_config: spanner_v1_messages.EncryptionConfig message, or None for
      Google-managed encryption.

  Returns:
    set[str]: The set of KMS key names with trailing '/cryptoKeyVersions/<N>'
      stripped (empty set for GMEK).
  """
  if encryption_config is None:
    return set()
  raw_keys = []
  if encryption_config.kmsKeyName:
    raw_keys.append(encryption_config.kmsKeyName)
  if encryption_config.kmsKeyNames:
    raw_keys.extend(encryption_config.kmsKeyNames)
  return GetDesiredEncryptionKeys(raw_keys)


def IsTransientError(err):
  """Returns True if err is a transient error during GetDatabase polling."""
  # apitools HttpError subclasses CommunicationError, so check it first.
  if isinstance(err, apitools_exceptions.HttpError):
    return err.status_code in _TRANSIENT_HTTP_STATUS_CODES
  if isinstance(err, requests.exceptions.SSLError):
    return False
  return isinstance(
      err,
      (
          apitools_exceptions.CommunicationError,
          google_auth_exceptions.TransportError,
          requests.exceptions.ConnectionError,
          requests.exceptions.Timeout,
          requests.exceptions.ChunkedEncodingError,
          ConnectionError,
          TimeoutError,
      ),
  )


def MinimumReencryptionWaitMs(
    required_consecutive_polls=DEFAULT_CONSECUTIVE_POLLS,
    sleep_ms=REENCRYPTION_SLEEP_MS,
    wait_ceiling_ms=REENCRYPTION_WAIT_CEILING_MS,
):
  """Returns the worst-case sum of inter-poll sleeps for N consecutive polls.

  Returns the sum of the worst-case inter-poll sleeps (maximum jitter added,
  then the ceiling applied) between required_consecutive_polls polls. Used as a
  minimum for max_wait_ms. It excludes RPC latency and the pre-start sleep, and
  retry jitter is random in [0, jitter_ms), so a max_wait_ms at exactly this
  value is not guaranteed to succeed.

  Args:
    required_consecutive_polls: Number of consecutive matching polls required.
    sleep_ms: Initial sleep duration between polls in milliseconds.
    wait_ceiling_ms: Maximum sleep duration between polls in milliseconds.

  Returns:
    int: Minimum max_wait_ms needed for required_consecutive_polls.
  """
  return int(
      round(
          sum(
              min(
                  sleep_ms * _EXPONENTIAL_SLEEP_MULTIPLIER**r + _JITTER_MS,
                  wait_ceiling_ms,
              )
              for r in range(required_consecutive_polls - 1)
          )
      )
  )


def _TargetMismatchMessage(actual_keys, target_keys):
  """Returns the ReencryptionTargetMismatchError message for the key sets."""
  return (
      "The database's encryptionConfig {!r} does not match the "
      'requested target {!r}. Check the --kms-keys/--clear-kms-keys '
      'value, or wait for the update operation to finish.'.format(
          sorted(actual_keys or []),
          sorted(target_keys or []),
      )
  )


class ReencryptionPoller(waiter.OperationPoller):
  """Poller that waits for Spanner database CMEK re-encryption convergence."""

  def __init__(
      self,
      target_keys,
      required_consecutive_polls=DEFAULT_CONSECUTIVE_POLLS,
      config_apply_grace_ms=DEFAULT_CONFIG_APPLY_GRACE_MS,
      max_transient_error_duration_ms=DEFAULT_MAX_TRANSIENT_ERROR_DURATION_MS,
      required_consecutive_divergent_polls=DEFAULT_CONSECUTIVE_DIVERGENT_POLLS,
      clock=time.monotonic,
  ):
    if required_consecutive_polls < 1:
      raise ReencryptionArgumentError(
          'required_consecutive_polls ({}) must be >= 1.'.format(
              required_consecutive_polls
          )
      )
    if required_consecutive_divergent_polls < 1:
      raise ReencryptionArgumentError(
          'required_consecutive_divergent_polls ({}) must be >= 1.'.format(
              required_consecutive_divergent_polls
          )
      )
    self.target_keys = GetDesiredEncryptionKeys(target_keys)
    self.required_consecutive_polls = required_consecutive_polls
    self.config_apply_grace_ms = config_apply_grace_ms
    self.max_transient_error_duration_ms = max_transient_error_duration_ms
    self.required_consecutive_divergent_polls = (
        required_consecutive_divergent_polls
    )
    self._clock = clock
    self.consecutive_matches = 0
    self._config_matched = False
    self._first_mismatch_time = None
    self._last_mismatched_config_keys = None
    self._config_match_time = None
    self._warned_key_form_mismatch = False
    self._consecutive_divergent_polls = 0
    self._consecutive_transient_errors = 0
    self._first_transient_error_time = None
    self._last_poll_start_time = None

  @property
  def has_unresolved_config_mismatch(self):
    """True if encryptionConfig was observed mismatching and never matched."""
    return self._first_mismatch_time is not None and not self._config_matched

  @property
  def last_mismatched_config_keys(self):
    """encryptionConfig key set from the most recent mismatch before any match."""
    return self._last_mismatched_config_keys

  def Poll(self, database_ref):
    """Calls databases.Get(database_ref), returning TRANSIENT on bounded blips."""
    poll_start = self._clock()
    try:
      database = databases.Get(database_ref)
    except Exception as err:  # pylint: disable=broad-except
      if IsTransientError(err):
        now = self._clock()
        if self._first_transient_error_time is None:
          self._first_transient_error_time = poll_start
        if (
            now - self._first_transient_error_time
        ) * 1000 > self.max_transient_error_duration_ms:
          log.warning(
              'Transient errors polling database %s for re-encryption '
              'exceeded max duration (%d ms); aborting. Last error: %s',
              database_ref,
              self.max_transient_error_duration_ms,
              err,
          )
          raise
        self._consecutive_transient_errors += 1
        log.debug(
            'Transient error polling database %s for re-encryption '
            '(consecutive=%d): %s',
            database_ref,
            self._consecutive_transient_errors,
            err,
        )
        if (
            self._consecutive_transient_errors
            == _TRANSIENT_ERROR_WARNING_THRESHOLD
        ):
          log.warning(
              'Encountered %d consecutive transient errors polling '
              'database %s for re-encryption; continuing to retry. '
              'Last error: %s',
              self._consecutive_transient_errors,
              database_ref,
              err,
          )
        return TRANSIENT
      raise
    self._last_poll_start_time = poll_start
    if self._first_transient_error_time is not None:
      transient_duration = max(
          0.0, poll_start - self._first_transient_error_time
      )
      if self._first_mismatch_time is not None:
        self._first_mismatch_time += transient_duration
      if self._config_match_time is not None:
        self._config_match_time += transient_duration
    self._consecutive_transient_errors = 0
    self._first_transient_error_time = None
    return database

  def IsDone(self, database):
    """Checks whether database encryptionInfo has converged for N polls."""
    if database is TRANSIENT:
      self.consecutive_matches = 0
      self._consecutive_divergent_polls = 0
      return False

    if database is None:
      self.consecutive_matches = 0
      self._consecutive_divergent_polls = 0
      return False

    actual = GetEncryptionConfigKeys(database.encryptionConfig)
    if actual != self.target_keys:
      if not self._config_matched:
        self._last_mismatched_config_keys = actual
        self.consecutive_matches = 0
        now = self._clock()
        if self._first_mismatch_time is None:
          self._first_mismatch_time = (
              self._last_poll_start_time
              if self._last_poll_start_time is not None
              else now
          )
        if (
            now - self._first_mismatch_time
        ) * 1000 > self.config_apply_grace_ms:
          raise ReencryptionTargetMismatchError(
              _TargetMismatchMessage(actual, self.target_keys)
          )
        return False
      self._consecutive_divergent_polls += 1
      self.consecutive_matches = 0
      if (
          self._consecutive_divergent_polls
          < self.required_consecutive_divergent_polls
      ):
        return False
      raise ReencryptionConfigDivergedError(
          'Database encryptionConfig diverged while waiting for '
          're-encryption: expected {!r}, observed {!r}. Another '
          'UpdateDatabase call may have changed the target encryption '
          'configuration.'.format(
              sorted(self.target_keys),
              sorted(actual),
          )
      )

    if not self._config_matched:
      self._config_match_time = (
          self._last_poll_start_time
          if self._last_poll_start_time is not None
          else self._clock()
      )
    self._config_matched = True
    self._consecutive_divergent_polls = 0

    converged_keys = GetConvergedEncryptionKeys(database)
    if converged_keys is not NOT_CONVERGED:
      self._MaybeWarnKeyFormMismatch(database, converged_keys)
    if (
        converged_keys is not NOT_CONVERGED
        and converged_keys == self.target_keys
    ):
      self.consecutive_matches += 1
      return self.consecutive_matches >= self.required_consecutive_polls

    self.consecutive_matches = 0
    return False

  def GetResult(self, database):
    """Returns the final converged Database message."""
    return database

  def _MaybeWarnKeyFormMismatch(self, database, converged_keys):
    """Logs a one-time warning if key names appear to differ only in form.

    Defensive: not expected with current Cloud KMS behavior, which reports key
    versions with the same project segment as the requested key name.

    Args:
      database: The polled Database message; its name is included in the
        warning.
      converged_keys: The KMS key names returned by GetConvergedEncryptionKeys.
    """
    if self._warned_key_form_mismatch:
      return
    # Comparing only unmatched keys catches partial multi-key mismatches;
    # requiring a project number on exactly one side excludes legitimate
    # cross-project key moves.
    unmatched_info = converged_keys - self.target_keys
    unmatched_target = self.target_keys - converged_keys
    if not unmatched_info or not unmatched_target:
      return
    info_by_suffix = {_StripProjectPrefix(k): k for k in unmatched_info}
    target_by_suffix = {_StripProjectPrefix(k): k for k in unmatched_target}
    if (
        len(info_by_suffix) != len(unmatched_info)
        or len(target_by_suffix) != len(unmatched_target)
        or info_by_suffix.keys() != target_by_suffix.keys()
    ):
      return
    if any(
        _HasProjectNumber(info_by_suffix[suffix])
        == _HasProjectNumber(target_by_suffix[suffix])
        for suffix in info_by_suffix
    ):
      return
    if (
        self._clock() - self._config_match_time
    ) * 1000 <= self.config_apply_grace_ms:
      return
    log.warning(
        'Database %s: encryptionInfo lists KMS key(s) %s, which differ from '
        'the requested target %s only in the project segment (project number '
        'vs. project ID). If this persists, the key names may be in different '
        'forms and the wait will not converge; compare '
        '`gcloud spanner databases describe` output with the --kms-keys value.',
        database.name or '',
        sorted(unmatched_info),
        sorted(unmatched_target),
    )
    self._warned_key_form_mismatch = True


def AwaitReencryption(
    database_ref,
    target_keys,
    message='Waiting for database re-encryption to converge',
    required_consecutive_polls=DEFAULT_CONSECUTIVE_POLLS,
    max_wait_ms=REENCRYPTION_MAX_WAIT_MS,
    sleep_ms=REENCRYPTION_SLEEP_MS,
    wait_ceiling_ms=REENCRYPTION_WAIT_CEILING_MS,
    config_apply_grace_ms=DEFAULT_CONFIG_APPLY_GRACE_MS,
    max_transient_error_duration_ms=DEFAULT_MAX_TRANSIENT_ERROR_DURATION_MS,
    required_consecutive_divergent_polls=DEFAULT_CONSECUTIVE_DIVERGENT_POLLS,
    clock=time.monotonic,
):
  """Waits until a database's physical encryption (encryptionInfo) converges.

  Allows Database.encryptionConfig to lag behind target_keys for up to
  config_apply_grace_ms before its first match (for example, when called
  immediately after an asynchronous UpdateDatabase request).

  KMS key names are compared as exact strings (with trailing
  '/cryptoKeyVersions/<N>' suffixes stripped). If encryptionInfo and target_keys
  ever differed only in project segment form (project number vs. project ID),
  ReencryptionPoller logs a one-time warning after config_apply_grace_ms.

  Args:
    database_ref: resources.Resource reference to the Spanner database.
    target_keys: Target KMS key resource name(s) (iterable of str, or None/empty
      for GMEK).
    message: Progress tracker message.
    required_consecutive_polls: Number of consecutive matching polls required to
      declare convergence (default 2; must be >= 1).
    max_wait_ms: Maximum wait time in milliseconds (default 4h = 14,400,000).
    sleep_ms: Initial sleep duration between polls in milliseconds (default
      10,000).
    wait_ceiling_ms: Maximum sleep duration between polls in milliseconds
      (default 30,000).
    config_apply_grace_ms: Grace period in milliseconds for encryptionConfig to
      first match target_keys (default 10m = 600,000).
    max_transient_error_duration_ms: Maximum duration in milliseconds for a
      continuous streak of transient polling errors before re-raising (default
      30m = 1,800,000).
    required_consecutive_divergent_polls: Number of consecutive polls with a
      diverged encryptionConfig (after an initial match) required before raising
      ReencryptionConfigDivergedError (default 2; must be >= 1).
    clock: Callable returning monotonic time in seconds (default
      time.monotonic).

  Returns:
    The converged Database message.

  Raises:
    ReencryptionArgumentError: If required_consecutive_polls < 1, if
      required_consecutive_divergent_polls < 1, or if max_wait_ms is less than
      MinimumReencryptionWaitMs(required_consecutive_polls, sleep_ms,
      wait_ceiling_ms).
    ReencryptionTargetMismatchError: If Database.encryptionConfig does not
      match target_keys within config_apply_grace_ms.
    ReencryptionConfigDivergedError: If Database.encryptionConfig matches
      target_keys and subsequently diverges for
      required_consecutive_divergent_polls consecutive polls.
    ReencryptionTimeoutError (a waiter.TimeoutError subclass): If convergence is
      not reached within max_wait_ms; config_mismatch_unresolved and
      last_mismatched_config_keys describe whether encryptionConfig was observed
      mismatching and never matched.
  """
  if required_consecutive_polls < 1:
    raise ReencryptionArgumentError(
        'required_consecutive_polls ({}) must be >= 1.'.format(
            required_consecutive_polls
        )
    )
  if required_consecutive_divergent_polls < 1:
    raise ReencryptionArgumentError(
        'required_consecutive_divergent_polls ({}) must be >= 1.'.format(
            required_consecutive_divergent_polls
        )
    )
  min_wait_ms = MinimumReencryptionWaitMs(
      required_consecutive_polls,
      sleep_ms=sleep_ms,
      wait_ceiling_ms=wait_ceiling_ms,
  )
  if max_wait_ms < min_wait_ms:
    raise ReencryptionArgumentError(
        'max_wait_ms ({}) must be at least MinimumReencryptionWaitMs({}, '
        'sleep_ms={}, wait_ceiling_ms={}) ({} ms).'.format(
            max_wait_ms,
            required_consecutive_polls,
            sleep_ms,
            wait_ceiling_ms,
            min_wait_ms,
        )
    )
  poller = ReencryptionPoller(
      target_keys=target_keys,
      required_consecutive_polls=required_consecutive_polls,
      config_apply_grace_ms=config_apply_grace_ms,
      max_transient_error_duration_ms=max_transient_error_duration_ms,
      required_consecutive_divergent_polls=required_consecutive_divergent_polls,
      clock=clock,
  )
  try:
    return waiter.WaitFor(
        poller,
        database_ref,
        message=message,
        max_wait_ms=max_wait_ms,
        exponential_sleep_multiplier=_EXPONENTIAL_SLEEP_MULTIPLIER,
        jitter_ms=_JITTER_MS,
        sleep_ms=sleep_ms,
        wait_ceiling_ms=wait_ceiling_ms,
    )
  except waiter.TimeoutError as exc:
    unresolved = poller.has_unresolved_config_mismatch
    raise ReencryptionTimeoutError(
        str(exc),
        config_mismatch_unresolved=unresolved,
        last_mismatched_config_keys=(
            poller.last_mismatched_config_keys if unresolved else None
        ),
    ) from exc


def Await(operation, message):
  """Wait for the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  poller = EmbeddedResponsePoller(
      client.projects_instances_databases_operations)
  ref = resources.REGISTRY.ParseRelativeName(
      operation.name,
      collection='spanner.projects.instances.databases.operations')
  return waiter.WaitFor(poller, ref, message)


def Cancel(instance, database, operation):
  """Cancel the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      operation,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance,
          'databasesId': database},
      collection='spanner.projects.instances.databases.operations')
  req = msgs.SpannerProjectsInstancesDatabasesOperationsCancelRequest(
      name=ref.RelativeName())
  return client.projects_instances_databases_operations.Cancel(req)


def Get(instance, database, operation):
  """Get the specified operation."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      operation,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance,
          'databasesId': database,
      },
      collection='spanner.projects.instances.databases.operations')
  req = msgs.SpannerProjectsInstancesDatabasesOperationsGetRequest(
      name=ref.RelativeName())
  return client.projects_instances_databases_operations.Get(req)


def List(instance, database, type_filter=None):
  """List operations on the database using the generic operation list API."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      database,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
          'instancesId': instance
      },
      collection='spanner.projects.instances.databases')
  req = msgs.SpannerProjectsInstancesDatabasesOperationsListRequest(
      name=ref.RelativeName()+'/operations',
      filter=type_filter)
  return list_pager.YieldFromList(
      client.projects_instances_databases_operations,
      req,
      field='operations',
      batch_size_attribute='pageSize')


def BuildDatabaseOperationTypeFilter(op_type):
  """Builds the filter for the different database operation metadata types."""
  if op_type == 'DATABASE':
    return ''

  base_string = 'metadata.@type:type.googleapis.com/google.spanner.admin.database.v1.'
  if op_type == 'DATABASE_RESTORE':
    return '({}OptimizeRestoredDatabaseMetadata) OR ({}RestoreDatabaseMetadata)'.format(
        base_string, base_string)

  if op_type == 'DATABASE_CREATE':
    return base_string + 'CreateDatabaseMetadata'

  if op_type == 'DATABASE_UPDATE_DDL':
    return base_string + 'UpdateDatabaseDdlMetadata'

  if op_type == 'DATABASE_CHANGE_QUORUM':
    return base_string + 'ChangeQuorumMetadata'


def ListDatabaseOperations(instance, database=None, type_filter=None):
  """List database operations using the Cloud Spanner specific API."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  instance_ref = resources.REGISTRY.Parse(
      instance,
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection='spanner.projects.instances')

  # When the database is passed in, use the generic list command, so no
  # operations are shown from previous incarnations of the database.
  if database:
    return List(instance, database, type_filter)

  req = msgs.SpannerProjectsInstancesDatabaseOperationsListRequest(
      parent=instance_ref.RelativeName(), filter=type_filter)
  return list_pager.YieldFromList(
      client.projects_instances_databaseOperations,
      req,
      field='operations',
      batch_size_attribute='pageSize')


class EmbeddedResponsePoller(waiter.CloudOperationPoller):
  """As CloudOperationPoller for polling, but uses the Operation.response."""

  def __init__(self, operation_service):
    self.operation_service = operation_service

  def GetResult(self, operation):
    return operation.response
