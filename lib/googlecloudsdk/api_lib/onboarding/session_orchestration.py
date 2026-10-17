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
) -> onboarding_messages.Session:
  """Handles a single pending user input and patches the session.

  Args:
    client: The useronboarding API client.
    messages: The useronboarding API messages module.
    session_id: The resource name of the session.
    pending_input: The PendingUserInput message to process.
    auto_accept_tos_ids: Optional list of TOS IDs to automatically accept
      without prompting.

  Returns:
    The updated session object returned from the patch call.

  Raises:
    onboarding_exceptions.OnboardingError: If the user input is unsupported or
      declined.
  """
  canonical_name = _CanonicalSessionName(session_id)
  if pending_input.tos:
    tos_acceptances = pending_input.tos.requiredTosAcceptances or []
    tos_ids = [tos.id for tos in tos_acceptances if tos.id]
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
          'Terms of Service declined. Onboarding cannot proceed.'
      )

    updated_session = messages.Session(tosAcceptances=accepted_acceptances)
    patch_request = messages.UseronboardingSessionsPatchRequest(
        name=canonical_name,
        session=updated_session,
        updateMask='tos_acceptances',
    )
    return client.sessions.Patch(patch_request)

  else:
    field_checks = [
        (pending_input.project, 'project selection'),
        (pending_input.billingAccount, 'billing account selection'),
        (pending_input.paymentInfo, 'payment information submission'),
        (pending_input.chargingStrategy, 'charging strategy selection'),
        (pending_input.makePayment, 'prepayment submission'),
        (pending_input.regionCode, 'region code selection'),
    ]
    unsupported = [label for condition, label in field_checks if condition]

    if unsupported:
      fields = ', '.join(unsupported)
      raise onboarding_exceptions.UnsupportedUserInputError(
          f'The session requires {fields}, which is not supported in this'
          ' version of the CLI.'
      )
    else:
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
  with progress_tracker.ProgressTracker('Processing onboarding step'):
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

  return session


def OrchestrateSession(
    session: onboarding_messages.Session,
    client: onboarding_client.UseronboardingV1alpha | None = None,
    messages: types.ModuleType | None = None,
    auto_accept_tos_ids: list[str] | None = None,
) -> onboarding_messages.Session:
  """Orchestrates an onboarding session to completion.

  Args:
    session: The initial session object to orchestrate.
    client: The useronboarding API client (optional).
    messages: The useronboarding API messages module (optional).
    auto_accept_tos_ids: Optional list of TOS IDs to automatically accept
      without prompting.

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
        raise onboarding_exceptions.SessionFailedError(
            f'Onboarding failed: {session.status.message}'
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
) -> onboarding_messages.Session:
  """Resolves and orchestrates an onboarding session to completion.

  Args:
    intent: The OnboardingIntent message.
    client: The useronboarding API client (optional).
    messages: The useronboarding API messages module (optional).
    auto_accept_tos_ids: Optional list of TOS IDs to automatically accept
      without prompting.

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
  )
