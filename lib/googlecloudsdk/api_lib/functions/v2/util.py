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
"""Functionality related to Cloud Functions v2 API clients."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import enum
import re

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
import frozendict
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.cloudresourcemanager import projects_util as projects_api_util
from googlecloudsdk.api_lib.functions.v2 import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker

from googlecloudsdk.core.util import encoding as encoder
from googlecloudsdk.core.util import retry
import six

_API_NAME = 'cloudfunctions'

_V2_ALPHA = 'v2alpha'
_V2_BETA = 'v2beta'
_V2_GA = 'v2'

RELEASE_TRACK_TO_API_VERSION = {
    calliope_base.ReleaseTrack.ALPHA: 'v2alpha',
    calliope_base.ReleaseTrack.BETA: 'v2beta',
    calliope_base.ReleaseTrack.GA: 'v2'
}

MAX_WAIT_MS = 1820000
SLEEP_MS = 1000

# EventArc types
EA_PUBSUB_MESSAGE_PUBLISHED = 'google.cloud.pubsub.topic.v1.messagePublished'
EA_STORAGE_ARCHIVE = 'google.cloud.storage.object.v1.archived'
EA_STORAGE_DELETE = 'google.cloud.storage.object.v1.deleted'
EA_STORAGE_FINALIZE = 'google.cloud.storage.object.v1.finalized'
EA_STORAGE_UPDATE = 'google.cloud.storage.object.v1.metadataUpdated'

EVENTARC_STORAGE_TYPES = (
    EA_STORAGE_ARCHIVE,
    EA_STORAGE_DELETE,
    EA_STORAGE_FINALIZE,
    EA_STORAGE_UPDATE,
)

# EventFlow types
EF_PUBSUB_MESSAGE_PUBLISH = 'google.pubsub.topic.publish'
EF_STORAGE_ARCHIVE = 'google.storage.object.archive'
EF_STORAGE_DELETE = 'google.storage.object.delete'
EF_STORAGE_FINALIZE = 'google.storage.object.finalize'
EF_STORAGE_METADATA_UPDATE = 'google.storage.object.metadataUpdate'

EVENTFLOW_TO_EVENTARC_STORAGE_MAP = frozendict.frozendict({
    EF_STORAGE_ARCHIVE: EA_STORAGE_ARCHIVE,
    EF_STORAGE_DELETE: EA_STORAGE_DELETE,
    EF_STORAGE_FINALIZE: EA_STORAGE_FINALIZE,
    EF_STORAGE_METADATA_UPDATE: EA_STORAGE_UPDATE,
})

# Legacy types
LEGACY_PUBSUB_MESSAGE_PUBLISH = (
    'providers/cloud.pubsub/eventTypes/topic.publish')

PUBSUB_MESSAGE_PUBLISH_TYPES = (
    EA_PUBSUB_MESSAGE_PUBLISHED,
    EF_PUBSUB_MESSAGE_PUBLISH,
    LEGACY_PUBSUB_MESSAGE_PUBLISH,
)


class ApiEnv(enum.Enum):
  TEST = 1
  AUTOPUSH = 2
  STAGING = 3
  PROD = 4


def GetProject():
  """Returns the value of the core/project config prooerty.

  Config properties can be overridden with command line flags. If the --project
  flag was provided, this will return the value provided with the flag.
  """
  return properties.VALUES.core.project.Get(required=True)


def GetMessagesModule(release_track):
  """Returns the API messages module for GCFv2."""
  api_version = RELEASE_TRACK_TO_API_VERSION.get(release_track)
  return apis.GetMessagesModule(_API_NAME, api_version)


def GetStage(messages):
  """Returns corresponding GoogleCloudFunctionsV2(alpha|beta|ga)Stage."""
  if messages is apis.GetMessagesModule(_API_NAME, _V2_ALPHA):
    return messages.GoogleCloudFunctionsV2alphaStage
  elif messages is apis.GetMessagesModule(_API_NAME, _V2_BETA):
    return messages.GoogleCloudFunctionsV2betaStage
  else:
    return messages.GoogleCloudFunctionsV2Stage


def GetStateMessage(messages):
  """Returns corresponding GoogleCloudFunctionsV2(alpha|beta|ga)stateMessage."""
  if messages is apis.GetMessagesModule(_API_NAME, _V2_ALPHA):
    return messages.GoogleCloudFunctionsV2alphaStateMessage
  elif messages is apis.GetMessagesModule(_API_NAME, _V2_BETA):
    return messages.GoogleCloudFunctionsV2betaStateMessage
  else:
    return messages.GoogleCloudFunctionsV2StateMessage


def GetClientInstance(release_track):
  """Returns an API client for GCFv2."""
  api_version = RELEASE_TRACK_TO_API_VERSION.get(release_track)
  return apis.GetClientInstance(_API_NAME, api_version)


def GetStateMessagesStrings(state_messages):
  """Returns the list of string representations of the state messages."""
  return map(lambda st: '[{}] {}'.format(str(st.severity), st.message),
             state_messages)


def _GetStageName(name_enum):
  """Converts NameValueValuesEnum into human-readable text."""
  return str(name_enum).replace('_', ' ').title()


def _BuildOperationMetadata(messages):
  """Returns corresponding GoogleCloudFunctionsV2(alpha|beta|ga)OperationMetadata.
  """
  if messages is apis.GetMessagesModule(_API_NAME, _V2_ALPHA):
    return messages.GoogleCloudFunctionsV2alphaOperationMetadata
  elif messages is apis.GetMessagesModule(_API_NAME, _V2_BETA):
    return messages.GoogleCloudFunctionsV2betaOperationMetadata
  elif messages is apis.GetMessagesModule(_API_NAME, _V2_GA):
    return messages.GoogleCloudFunctionsV2OperationMetadata
  else:
    raise NotImplementedError('Invalid messages module.')


def _GetOperationMetadata(messages, operation):
  return encoding.PyValueToMessage(
      _BuildOperationMetadata(messages),
      encoding.MessageToPyValue(operation.metadata))


def _GetOperation(client, request):
  """Get operation and return None if doesn't exist."""
  try:
    # We got response for a GET request, so an operation exists.
    return client.projects_locations_operations.Get(request)
  except apitools_exceptions.HttpError as error:
    if error.status_code == six.moves.http_client.NOT_FOUND:
      return None
    raise


def _GetStages(client, request, messages):
  """Returns None until stages have been loaded in the operation."""
  operation = _GetOperation(client, request)
  if operation.error:
    raise exceptions.StatusToFunctionsError(operation.error)

  if not operation.metadata:
    return None
  operation_metadata = _GetOperationMetadata(messages, operation)
  if not operation_metadata.stages:
    return None

  stages = []
  for stage in operation_metadata.stages:
    message = '[{}]'.format(_GetStageName(stage.name))
    stages.append(progress_tracker.Stage(message, key=str(stage.name)))
  return stages


def _GetOperationStatus(client, request, tracker, messages):
  """Returns a Boolean indicating whether the request has completed."""
  operation = client.projects_locations_operations.Get(request)
  if operation.error:
    raise exceptions.StatusToFunctionsError(
        operation.error, error_message=OperationErrorToString(operation.error))

  operation_metadata = _GetOperationMetadata(messages, operation)
  for stage in operation_metadata.stages:
    stage_in_progress = (
        stage.state is GetStage(messages).StateValueValuesEnum.IN_PROGRESS)
    stage_complete = (
        stage.state is GetStage(messages).StateValueValuesEnum.COMPLETE)

    if not stage_in_progress and not stage_complete:
      continue

    stage_key = str(stage.name)
    if tracker.IsComplete(stage_key):
      # Cannot update a completed stage in the tracker
      continue

    # Start running a stage
    if tracker.IsWaiting(stage_key):
      tracker.StartStage(stage_key)

    # Update stage message, including Build logs URL if applicable
    stage_message = stage.message or ''
    if stage_in_progress:
      stage_message = (stage_message or 'In progress') + '... '
    else:
      stage_message = ''

    if stage.resourceUri and stage_key == 'BUILD':
      stage_message += 'Logs are available at [{}]'.format(stage.resourceUri)

    tracker.UpdateStage(stage_key, stage_message)

    # Complete a finished stage
    if stage_complete:
      if stage.stateMessages:
        tracker.CompleteStageWithWarnings(
            stage_key, GetStateMessagesStrings(stage.stateMessages))
      else:
        tracker.CompleteStage(stage_key)
  return operation.done


def WaitForOperation(client,
                     messages,
                     operation,
                     description,
                     extra_stages=None):
  """Wait for a long-running operation (LRO) to complete.

  Args:
    client: The GCFv2 API client.
    messages: The GCFv2 message stubs.
    operation: The operation message response.
    description: str, the description of the waited operation.
    extra_stages: List[progress_tracker.Stage]|None, list of optional stages for
      the progress tracker to watch. The GCF 2nd api returns unexpected stages
      in the case of rollbacks.
  """
  request = messages.CloudfunctionsProjectsLocationsOperationsGetRequest(
      name=operation.name)
  # Wait for stages to be loaded.
  with progress_tracker.ProgressTracker('Preparing function') as tracker:
    retryer = retry.Retryer(max_wait_ms=MAX_WAIT_MS)
    try:
      # List[progress_tracker.Stage]
      stages = retryer.RetryOnResult(
          _GetStages,
          args=[client, request, messages],
          should_retry_if=None,
          sleep_ms=SLEEP_MS)
    except retry.WaitException:
      raise exceptions.FunctionsError('Operation {0} is taking too long'.format(
          request.name))

  if extra_stages is not None:
    stages += extra_stages

  # Wait for LRO to complete.
  description += '...'
  with progress_tracker.StagedProgressTracker(description, stages) as tracker:
    retryer = retry.Retryer(max_wait_ms=MAX_WAIT_MS)
    try:
      retryer.RetryOnResult(
          _GetOperationStatus,
          args=[client, request, tracker, messages],
          should_retry_if=False,
          sleep_ms=SLEEP_MS)
    except retry.WaitException:
      raise exceptions.FunctionsError('Operation {0} is taking too long'.format(
          request.name))


def FormatTimestamp(timestamp):
  """Formats a timestamp which will be presented to a user.

  Args:
    timestamp: Raw timestamp string in RFC3339 UTC "Zulu" format.

  Returns:
    Formatted timestamp string.
  """
  return re.sub(r'(\.\d{3})\d*Z$', r'\1', timestamp.replace('T', ' '))


def OperationErrorToString(error):
  """Returns a human readable string representation from the operation.

  Args:
    error: A string representing the raw json of the operation error.

  Returns:
    A human readable string representation of the error.
  """
  error_message = 'OperationError: code={0}, message={1}'.format(
      error.code, encoder.Decode(error.message))
  messages = apis.GetMessagesModule('cloudfunctions', _V2_ALPHA)
  if error.details:
    for detail in error.details:
      sub_error = encoding.PyValueToMessage(messages.Status,
                                            encoding.MessageToPyValue(detail))
      if sub_error.code is not None or sub_error.message is not None:
        error_message += '\n' + OperationErrorToString(sub_error)
  return error_message


def HasRoleBinding(sa_email, role):
  # type(str, str) -> bool
  """Returns whether the given service account has the given role bound.

  Args:
    sa_email: The service account to check.
    role: The role to check for.
  """
  iam_policy = projects_api.GetIamPolicy(
      projects_util.ParseProject(GetProject()))

  # iam_policy.bindings structure:
  # list[<Binding
  #       members=['serviceAccount:member@thing.iam.gserviceaccount.com', ...],
  #       role='roles/somerole'>...]
  return any(
      'serviceAccount:{}'.format(sa_email) in b.members and b.role == role
      for b in iam_policy.bindings)


def PromptToBindRoleIfMissing(sa_email, role, reason=''):
  # type: (str, str, str) -> None
  """Prompts to bind the role to the service account if missing.

  If the console cannot prompt, a warning is logged instead.

  Args:
    sa_email: The service account email to bind the role to.
    role: The role to bind if missing.
    reason: Extra information to print explaining why the binding is necessary.
  """
  if HasRoleBinding(sa_email, role):
    return

  log.status.Print('Service account [{}] is missing the role [{}].\n{}'.format(
      sa_email, role, reason))

  bind = console_io.CanPrompt() and console_io.PromptContinue(
      prompt_string='\nBind the role [{}] to service account [{}]?'.format(
          role, sa_email))
  if not bind:
    log.warning('Manual binding of above role may be necessary.\n')
    return

  project_ref = projects_util.ParseProject(GetProject())
  member = 'serviceAccount:{}'.format(sa_email)
  try:
    projects_api.AddIamPolicyBinding(project_ref, member, role)
    log.status.Print('Role successfully bound.\n')
  except apitools_exceptions.HttpForbiddenError:
    log.warning(
        'Your account does not have permission to add roles to the service '
        'account [%s]. If the deployment fails, ensure [%s] has the role '
        '[%s] before retrying.', sa_email, sa_email, role)


def _LookupAuditConfig(iam_policy, service):
  """Returns the audit config for the given service if it exists."""
  # iam_policy.auditConfigs structure:
  # list[<AuditConfig
  #       auditLogConfigs=[<AuditLogConfig<logType=...>, ...],
  #       service='foo.googleapis.com'>...]
  for ac in iam_policy.auditConfigs:
    if ac.service == service:
      return ac

  return None


_rm_messages = projects_api_util.GetMessages()

_LOG_TYPES = frozenset([
    _rm_messages.AuditLogConfig.LogTypeValueValuesEnum.ADMIN_READ,
    _rm_messages.AuditLogConfig.LogTypeValueValuesEnum.DATA_READ,
    _rm_messages.AuditLogConfig.LogTypeValueValuesEnum.DATA_WRITE,
])


def HasDataAccessAuditLogsFullyEnabled(service):
  # type(str) -> bool
  """Returns whether audit logs are fully enabled for the given service.

  Args:
    service: The service to look up. E.g.: foo.googleapis.com.

  Returns:
    whether audit logs are fully enabled for the given service.
  """
  iam_policy = projects_api.GetIamPolicy(
      projects_util.ParseProject(GetProject()))
  audit_config = _LookupAuditConfig(iam_policy, service)
  enabled_log_types = ([] if not audit_config else
                       [lc.logType for lc in audit_config.auditLogConfigs])

  return all([lt in enabled_log_types for lt in _LOG_TYPES])


def PromptToEnableDataAccessAuditLogs(service):
  # type: (str) -> None
  """Prompts to enable Data Access audit logs for the given service.

  If the console cannot prompt, a warning is logged instead.

  Args:
    service: The service to enable Data Access audit logs for.
  """
  if HasDataAccessAuditLogsFullyEnabled(service):
    return

  project = GetProject()
  log.status.Print(
      'Some Data Access audit logs are disabled for [{}]: '
      'https://console.cloud.google.com/iam-admin/audit?project={}'.format(
          service, project))

  enable = console_io.CanPrompt() and console_io.PromptContinue(
      prompt_string='\nEnable all Data Access audit logs for [{}]?'.format(
          service))
  if not enable:
    log.warning(
        'Manual enablement of Data Access audit logs may be necessary.\n')
    return

  project_ref = projects_util.ParseProject(project)
  policy = projects_api.GetIamPolicy(project_ref)

  audit_config = _LookupAuditConfig(policy, service)

  # Create the audit config for the service if missing
  if not audit_config:
    audit_config = _rm_messages.AuditConfig(service=service, auditLogConfigs=[])
    policy.auditConfigs.append(audit_config)

  # Create log configs for any missing log types:
  enabled_log_types = [lc.logType for lc in audit_config.auditLogConfigs]
  log_types_to_enable = [lt for lt in _LOG_TYPES if lt not in enabled_log_types]
  audit_config.auditLogConfigs.extend(
      [_rm_messages.AuditLogConfig(logType=lt) for lt in log_types_to_enable])

  try:
    projects_api.SetIamPolicy(project_ref, policy, update_mask='auditConfigs')
    log.status.Print('Data Access audit logs successfully enabled.')
  except apitools_exceptions.HttpForbiddenError:
    log.warning(
        'Your account does not have permission to enable Data Access audit '
        'logs for the service [%s]. If the deployment fails, ensure audit '
        'logs are enabled for service [%s] before retrying', service, service)


def GetCloudFunctionsApiEnv():
  """Determine the cloudfunctions API env the gcloud cmd is using."""
  endpoint_property = getattr(properties.VALUES.api_endpoint_overrides,
                              'cloudfunctions')
  api_string = endpoint_property.Get()
  if api_string is None:
    return ApiEnv.PROD
  if 'test-cloudfunctions' in api_string:
    return ApiEnv.TEST
  if 'autopush-cloudfunctions' in api_string:
    return ApiEnv.AUTOPUSH
  if 'staging-cloudfunctions' in api_string:
    return ApiEnv.STAGING

  return ApiEnv.PROD
