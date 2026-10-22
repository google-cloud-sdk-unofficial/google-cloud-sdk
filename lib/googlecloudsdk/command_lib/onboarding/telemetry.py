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
"""Telemetry helpers for onboarding gcloud commands.

Funnel events are recorded as Calliope custom key/value metrics and land in
Concord alongside the command's other client-side events (sharing the same
obscured_session_uuid). Resolved session attribution is sent via the typed
OnboardingPlatformExtension proto field on a CustomBeacon so that session_id
(ST_GOOGLE_GENERATED_USER_METADATA) is pseudonymized by Concord identically to
OaaS backend (OnboardingSessionEvent) and frontend (OnboardingPlatformExtension)
events.

Command failures are intentionally not recorded here: Calliope already records
the exception type of any error raised by the command.
"""

from __future__ import annotations

import json

from googlecloudsdk.core import config
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import platforms

# Custom metric keys. All keys are prefixed to make them easy to filter in the
# shared gcloud client-side events table.
XP_ID_KEY = 'onboarding_xp_id'
PENDING_INPUT_KEY = 'onboarding_pending_input'
UNSUPPORTED_PENDING_INPUT_KEY = 'onboarding_unsupported_pending_input'
TOS_DECISION_KEY = 'onboarding_tos_decision'
UNRECOGNIZED_TOS_ID_KEY = 'onboarding_unrecognized_tos_id'
PROJECT_DECISION_KEY = 'onboarding_project_decision'
CLOUD_REGION_DECISION_KEY = 'onboarding_cloud_region_decision'

# Span name for time spent polling a session in the PROCESSING state. Must
# match the pattern "[a-zA-Z0-9_]+".
PROCESSING_SPAN = 'onboarding_session_processing'

# Values for PENDING_INPUT_KEY.
PENDING_INPUT_TOS = 'tos'
PENDING_INPUT_PROJECT = 'project'
PENDING_INPUT_CLOUD_REGION = 'cloud_region'

# Values for UNSUPPORTED_PENDING_INPUT_KEY.
PENDING_INPUT_BILLING_ACCOUNT = 'billing_account'
PENDING_INPUT_PAYMENT_INFO = 'payment_info'
PENDING_INPUT_CHARGING_STRATEGY = 'charging_strategy'
PENDING_INPUT_MAKE_PAYMENT = 'make_payment'
PENDING_INPUT_REGION_CODE = 'region_code'
PENDING_INPUT_UNKNOWN = 'unknown'

# Values for the *_DECISION_KEY keys, shared by all user inputs. Not every
# input records every value.
# The user confirmed at the prompt (accepted the ToS or selected an option).
DECISION_CONFIRMED = 'confirmed'
# The user declined or cancelled at the prompt.
DECISION_DECLINED = 'declined'
# The only available option was selected without prompting.
DECISION_AUTO_SELECTED = 'auto_selected'
# The decision was provided via a flag (e.g. --auto-accept-tos-ids, --region)
# without prompting.
DECISION_FLAG = 'flag'
# The value provided via a flag is not one of the available options.
DECISION_FLAG_INVALID = 'flag_invalid'
# Prompts were unavailable (e.g. --quiet, core/disable_prompts or a
# non-interactive terminal), so either the prompt default was applied without
# an explicit user decision, or the command failed because an explicit
# decision is required.
DECISION_UNATTENDED = 'unattended'

# gcloud-disable-gdu-domain
_CLEARCUT_PROTO3_ENDPOINT = 'https://play.googleapis.com/log?format=json_proto3'
_ONBOARDING_EXTENSION_KEY = (
    '[logs.proto.cloud.concord.onboarding_platform_extension]'
)
_INTEGRATOR = 'gcloud'
_SESSION_NAME_PREFIX = 'sessions/'


def RecordEvent(key: str, value: str) -> None:
  """Records a custom key/value metric for the current command."""
  metrics.CustomKeyValue(
      properties.VALUES.metrics.command_name.Get(), key, value
  )


def RecordSessionResolved(session_name: str, xp_id: str | None) -> None:
  """Records resolved OaaS session metadata via OnboardingPlatformExtension.

  Args:
    session_name: The session resource name (e.g. 'sessions/<uuid>') or raw
      session ID.
    xp_id: The experience ID the session was resolved for.
  """
  cid = metrics.GetCIDIfMetricsEnabled()
  if not cid:
    return  # Respects usage_reporting=False opt-out.

  session_id = session_name or ''
  if session_id.startswith(_SESSION_NAME_PREFIX):
    session_id = session_id[len(_SESSION_NAME_PREFIX) :]

  extension_payload: dict[str, object] = {
      'session_id': session_id,
      'integrator': _INTEGRATOR,
  }
  if xp_id:
    extension_payload['experience_id'] = xp_id

  now_ms = metrics.GetTimeMillis()
  concord_event: dict[str, object] = {
      'console_type': 'CloudSDK',
      'client_install_id': cid,
      'release_version': config.CLOUD_SDK_VERSION,
      'event_type': 'Custom',
      'event_name': properties.VALUES.metrics.command_name.Get(),
      _ONBOARDING_EXTENSION_KEY: extension_payload,
  }
  if xp_id:
    concord_event['event_metadata'] = [{'key': XP_ID_KEY, 'value': xp_id}]

  request_body = json.dumps(
      {
          'client_info': {
              'client_type': 'DESKTOP',
              'desktop_client_info': {
                  'os': platforms.Platform.Current().operating_system.id,
              },
          },
          'log_source_name': 'CONCORD',
          'zwieback_cookie': cid,
          'request_time_ms': now_ms,
          'log_event': [{
              'source_extension_json': json.dumps(
                  concord_event, sort_keys=True
              ),
              'event_time_ms': now_ms,
          }],
      },
      sort_keys=True,
  )
  headers = {'user-agent': metrics.GetUserAgentIfMetricsEnabled() or ''}
  metrics.CustomBeacon(_CLEARCUT_PROTO3_ENDPOINT, 'POST', request_body, headers)


def RecordProcessingDuration():
  """Returns a context manager that times polling of a processing session."""
  return metrics.RecordDuration(PROCESSING_SPAN)
