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
"""Helper for orchestrating onboarding sessions in gcloud commands."""

from __future__ import annotations

import time
import types
from typing import TYPE_CHECKING

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.onboarding import exceptions as onboarding_exceptions
from googlecloudsdk.command_lib.onboarding import telemetry
from googlecloudsdk.command_lib.onboarding import user_inputs
from googlecloudsdk.core import log
from googlecloudsdk.core.console import progress_tracker

if TYPE_CHECKING:
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.generated_clients.apis.useronboarding.v1alpha import useronboarding_v1alpha_client as onboarding_client
  from googlecloudsdk.generated_clients.apis.useronboarding.v1alpha import useronboarding_v1alpha_messages as onboarding_messages

# How long to wait between polls while a session is being processed.
_POLL_INTERVAL_SECONDS = 2


def _CanonicalSessionName(session_id: str) -> str:
  """Ensures the session ID is formatted as a full resource name."""
  if session_id and not session_id.startswith('sessions/'):
    return f'sessions/{session_id}'
  return session_id


def _ProcessPendingUserInput(
    client: onboarding_client.UseronboardingV1alpha,
    messages: types.ModuleType,
    session_id: str,
    pending_input: onboarding_messages.PendingUserInput,
    auto_accept_tos_ids: list[str] | None = None,
    selected_region_name: str | None = None,
) -> onboarding_messages.Session:
  """Handles a single pending user input and patches the session.

  Args:
    client: The useronboarding API client.
    messages: The useronboarding API messages module.
    session_id: The resource name of the session.
    pending_input: The PendingUserInput message to process.
    auto_accept_tos_ids: Optional list of TOS IDs to automatically accept
      without prompting.
    selected_region_name: Optional name of the Google Cloud region to select
      without prompting, if a region selection is required.

  Returns:
    The updated session object returned from the patch call.

  Raises:
    onboarding_exceptions.OnboardingError: If the user input is unsupported or
      declined.
  """
  canonical_name = _CanonicalSessionName(session_id)
  if pending_input.tos:
    telemetry.RecordEvent(
        telemetry.PENDING_INPUT_KEY, telemetry.PENDING_INPUT_TOS
    )
    tos_acceptances = pending_input.tos.requiredTosAcceptances or []
    tos_ids = [tos.id for tos in tos_acceptances if tos.id]
    # Validate against the server's required ToS list (not just the local
    # registry) so unknown IDs are attributed correctly: a required ID this
    # gcloud does not recognize means gcloud is outdated, whereas an
    # unrecognized `--auto-accept-tos-ids` value that the server does not
    # require is an invalid flag value.
    unsupported_ids = user_inputs.GetUnsupportedTosIds(tos_ids)
    if unsupported_ids:
      raise user_inputs.UnsupportedTosIdError(
          user_inputs.FormatUnsupportedToSError(unsupported_ids)
      )
    if auto_accept_tos_ids:
      user_inputs.ValidateTosIds(auto_accept_tos_ids)
    accepted_ids = set(
        user_inputs.HandleUserInputToS(
            tos_ids, auto_accept_tos_ids=auto_accept_tos_ids
        )
    )
    accepted_acceptances = [
        tos for tos in tos_acceptances if tos.id in accepted_ids
    ]
    if len(accepted_acceptances) != len(tos_ids):
      raise onboarding_exceptions.TermsOfServiceDeclinedError(
          user_inputs.FormatDeclinedToSError(tos_ids)
      )

    updated_session = messages.Session(tosAcceptances=accepted_acceptances)
    patch_request = messages.UseronboardingSessionsPatchRequest(
        name=canonical_name,
        session=updated_session,
        updateMask='tos_acceptances',
    )
    return client.sessions.Patch(patch_request)

  elif pending_input.project:
    telemetry.RecordEvent(
        telemetry.PENDING_INPUT_KEY, telemetry.PENDING_INPUT_PROJECT
    )
    supported_projects = pending_input.project.supportedProjects or []
    if not supported_projects:
      raise onboarding_exceptions.SessionProtocolError(
          'An error occurred. Please visit the Cloud Console'
          ' (https://console.cloud.google.com) to select a project.'
      )
    selected_project = user_inputs.HandleUserInputSelectProject(
        supported_projects
    )
    if selected_project is None:
      raise onboarding_exceptions.ProjectNotSelectedError(
          'No project selected. Onboarding cannot proceed.'
      )

    updated_session = messages.Session(project=selected_project)
    patch_request = messages.UseronboardingSessionsPatchRequest(
        name=canonical_name,
        session=updated_session,
        updateMask='project',
    )
    return client.sessions.Patch(patch_request)

  elif pending_input.cloudRegion:
    telemetry.RecordEvent(
        telemetry.PENDING_INPUT_KEY, telemetry.PENDING_INPUT_CLOUD_REGION
    )
    supported_regions = pending_input.cloudRegion.supportedRegions or []
    if not supported_regions:
      raise onboarding_exceptions.SessionProtocolError(
          'An error occurred. Please visit the Cloud Console'
          ' (https://console.cloud.google.com) to get a project.'
      )
    selected_region = user_inputs.HandleUserInputSelectCloudRegion(
        supported_regions,
        default_region=pending_input.cloudRegion.defaultRegion,
        selected_region_name=selected_region_name,
    )
    if selected_region is None:
      raise onboarding_exceptions.CloudRegionNotSelectedError(
          'No region selected. Onboarding cannot proceed.'
      )

    updated_session = messages.Session(cloudRegion=selected_region)
    patch_request = messages.UseronboardingSessionsPatchRequest(
        name=canonical_name,
        session=updated_session,
        updateMask='cloud_region',
    )
    return client.sessions.Patch(patch_request)

  else:
    field_checks = [
        (
            pending_input.billingAccount,
            'billing account selection',
            telemetry.PENDING_INPUT_BILLING_ACCOUNT,
        ),
        (
            pending_input.paymentInfo,
            'payment information submission',
            telemetry.PENDING_INPUT_PAYMENT_INFO,
        ),
        (
            pending_input.chargingStrategy,
            'charging strategy selection',
            telemetry.PENDING_INPUT_CHARGING_STRATEGY,
        ),
        (
            pending_input.makePayment,
            'prepayment submission',
            telemetry.PENDING_INPUT_MAKE_PAYMENT,
        ),
        (
            pending_input.regionCode,
            'region code selection',
            telemetry.PENDING_INPUT_REGION_CODE,
        ),
    ]
    unsupported = [
        (label, event) for condition, label, event in field_checks if condition
    ]

    if unsupported:
      for _, event in unsupported:
        telemetry.RecordEvent(telemetry.UNSUPPORTED_PENDING_INPUT_KEY, event)
      fields = ', '.join(label for label, _ in unsupported)
      raise onboarding_exceptions.UnsupportedUserInputError(
          f'The session requires {fields}, which is not supported in this'
          ' version of the CLI.'
      )
    else:
      telemetry.RecordEvent(
          telemetry.UNSUPPORTED_PENDING_INPUT_KEY,
          telemetry.PENDING_INPUT_UNKNOWN,
      )
      raise onboarding_exceptions.UnsupportedUserInputError(
          'Unsupported pending user input required.'
      )


def _WaitForProcessing(
    client: onboarding_client.UseronboardingV1alpha,
    messages: types.ModuleType,
    session_id: str,
) -> onboarding_messages.Session:
  """Polls the session while it is in the PROCESSING state.

  Args:
    client: The useronboarding API client.
    messages: The useronboarding API messages module.
    session_id: The resource name of the session.

  Returns:
    The session object once it transitions out of PROCESSING.
  """
  canonical_name = _CanonicalSessionName(session_id)
  with (
      progress_tracker.ProgressTracker('Processing onboarding step'),
      telemetry.RecordProcessingDuration(),
  ):
    while True:
      time.sleep(_POLL_INTERVAL_SECONDS)
      get_request = messages.UseronboardingSessionsGetRequest(
          name=canonical_name
      )
      session = client.sessions.Get(get_request)
      if (
          session.status.code
          != messages.SessionStatus.CodeValueValuesEnum.PROCESSING
      ):
        return session


def ResolveSession(
    intent: onboarding_messages.OnboardingIntent,
    client: onboarding_client.UseronboardingV1alpha | None = None,
    messages: types.ModuleType | None = None,
) -> onboarding_messages.Session:
  """Resolves an onboarding session from an intent.

  Args:
    intent: The OnboardingIntent message.
    client: The useronboarding API client (optional).
    messages: The useronboarding API messages module (optional).

  Returns:
    The resolved session object.
  """
  if client is None:
    client = apis.GetClientInstance('useronboarding', 'v1alpha')
  if messages is None:
    messages = apis.GetMessagesModule('useronboarding', 'v1alpha')

  request = messages.ResolveSessionRequest(intent=intent)
  with progress_tracker.ProgressTracker('Resolving onboarding session'):
    response = client.sessions.ResolveSession(request)
    session = response.session

  telemetry.RecordSessionResolved(session.name, intent.xpId)
  return session


def OrchestrateSession(
    session: onboarding_messages.Session,
    client: onboarding_client.UseronboardingV1alpha | None = None,
    messages: types.ModuleType | None = None,
    auto_accept_tos_ids: list[str] | None = None,
    selected_region_name: str | None = None,
) -> onboarding_messages.Session:
  """Orchestrates an onboarding session to completion.

  Args:
    session: The initial session object to orchestrate.
    client: The useronboarding API client (optional).
    messages: The useronboarding API messages module (optional).
    auto_accept_tos_ids: Optional list of TOS IDs to automatically accept
      without prompting.
    selected_region_name: Optional name of the Google Cloud region to select
      without prompting, if a region selection is required.

  Returns:
    The completed session object.

  Raises:
    onboarding_exceptions.OnboardingError: If the onboarding fails or
      encounters unsupported inputs.
  """
  if client is None:
    client = apis.GetClientInstance('useronboarding', 'v1alpha')
  if messages is None:
    messages = apis.GetMessagesModule('useronboarding', 'v1alpha')

  status_enum = messages.SessionStatus.CodeValueValuesEnum
  while True:
    match session.status.code:
      case status_enum.COMPLETED:
        log.status.Print('Onboarding completed successfully!')
        return session
      case status_enum.FAILED:
        error_detail = session.status.message
        if (
            not error_detail
            and session.status.error
            and session.status.error.reason
        ):
          error_detail = session.status.error.reason
        raise onboarding_exceptions.SessionFailedError(
            f'Onboarding failed: {error_detail or "Unknown error"}'
        )
      case status_enum.PROCESSING:
        session = _WaitForProcessing(client, messages, session.name)
      case status_enum.PENDING_USER_INPUT:
        if not session.pendingUserInputs:
          raise onboarding_exceptions.SessionProtocolError(
              'Session is pending user input but the server specified none.'
          )

        pending_input = session.pendingUserInputs[0]
        session = _ProcessPendingUserInput(
            client,
            messages,
            session.name,
            pending_input,
            auto_accept_tos_ids=auto_accept_tos_ids,
            selected_region_name=selected_region_name,
        )
      case unexpected_status:
        raise onboarding_exceptions.SessionProtocolError(
            f'Encountered unexpected session status: {unexpected_status}'
        )


def ResolveAndOrchestrateSession(
    intent: onboarding_messages.OnboardingIntent,
    client: onboarding_client.UseronboardingV1alpha | None = None,
    messages: types.ModuleType | None = None,
    auto_accept_tos_ids: list[str] | None = None,
    selected_region_name: str | None = None,
) -> onboarding_messages.Session:
  """Resolves and orchestrates an onboarding session to completion.

  Args:
    intent: The OnboardingIntent message.
    client: The useronboarding API client (optional).
    messages: The useronboarding API messages module (optional).
    auto_accept_tos_ids: Optional list of TOS IDs to automatically accept
      without prompting.
    selected_region_name: Optional name of the Google Cloud region to select
      without prompting, if a region selection is required.

  Returns:
    The completed session object.
  """
  if client is None:
    client = apis.GetClientInstance('useronboarding', 'v1alpha')
  if messages is None:
    messages = apis.GetMessagesModule('useronboarding', 'v1alpha')

  session = ResolveSession(intent, client=client, messages=messages)
  return OrchestrateSession(
      session,
      client=client,
      messages=messages,
      auto_accept_tos_ids=auto_accept_tos_ids,
      selected_region_name=selected_region_name,
  )
