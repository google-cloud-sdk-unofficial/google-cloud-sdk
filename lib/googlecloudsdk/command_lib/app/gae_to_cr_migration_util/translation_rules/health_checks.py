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
"""Translation rules for health checks from GAE to Cloud Run."""

from collections.abc import Mapping, Sequence
from typing import Any
_GAE_TO_CR_PROBE_KEY_MAP = {
    'path': 'httpGet.path',
    'timeout_sec': 'timeoutSeconds',
    'check_interval_sec': 'periodSeconds',
    'failure_threshold': 'failureThreshold',
    'success_threshold': 'successThreshold',
    'initial_delay_sec': 'initialDelaySeconds',
}

# Supported keys for Cloud Run probes as defined in
# googlecloudsdk.command_lib.run.flags
_LIVENESS_PROBE_KEYS = (
    'initialDelaySeconds',
    'timeoutSeconds',
    'periodSeconds',
    'failureThreshold',
    'httpGet.path',
)
_READINESS_PROBE_KEYS = (
    'timeoutSeconds',
    'periodSeconds',
    'failureThreshold',
    'successThreshold',
    'httpGet.path',
)


def _translate_check(
    *,
    input_flatten_as_appyaml: Mapping[str, Any],
    check_name: str,
    flag_name: str,
    default_period: int,
    supported_keys: Sequence[str],
) -> Sequence[str]:
  """Translates GAE health checks to Cloud Run probe flags."""
  if check_name not in (key.split('.')[0] for key in input_flatten_as_appyaml):
    return []

  # Default values for GAE Flex health checks
  # https://cloud.google.com/appengine/docs/flexible/reference/app-yaml#health_checks
  defaults = {
      'path': '/_ah/health',
      'timeout_sec': 4,
      'check_interval_sec': default_period,
      'failure_threshold': 2,
      'success_threshold': 2,
      'initial_delay_sec': 0,
  }

  probe_parts = []
  for gae_key, cr_key in _GAE_TO_CR_PROBE_KEY_MAP.items():
    if cr_key in supported_keys:
      value = input_flatten_as_appyaml.get(
          f'{check_name}.{gae_key}', defaults.get(gae_key)
      )
      if value is not None:
        probe_parts.append(f'{cr_key}={value}')

  if not probe_parts:
    return []

  return [f'{flag_name}={",".join(probe_parts)}']


def _translate_liveness_check(
    input_flatten_as_appyaml: Mapping[str, Any],
) -> Sequence[str]:
  """Translates GAE liveness_check to Cloud Run --liveness-probe flag.

  Args:
    input_flatten_as_appyaml: A flattened mapping of the input data, with keys
      translated to their app.yaml equivalents.

  Returns:
    A sequence of strings representing the Cloud Run liveness probe flag.
  """
  return _translate_check(
      input_flatten_as_appyaml=input_flatten_as_appyaml,
      check_name='liveness_check',
      flag_name='--liveness-probe',
      default_period=30,
      supported_keys=_LIVENESS_PROBE_KEYS,
  )


def _translate_readiness_check(
    input_flatten_as_appyaml: Mapping[str, Any],
) -> Sequence[str]:
  """Translates GAE readiness_check to Cloud Run --readiness-probe flag.

  Args:
    input_flatten_as_appyaml: A flattened mapping of the input data, with keys
      translated to their app.yaml equivalents.

  Returns:
    A sequence of strings representing the Cloud Run readiness probe flag.
  """
  return _translate_check(
      input_flatten_as_appyaml=input_flatten_as_appyaml,
      check_name='readiness_check',
      flag_name='--readiness-probe',
      default_period=5,
      supported_keys=_READINESS_PROBE_KEYS,
  )


def translate_all_health_checks(
    input_flatten_as_appyaml: Mapping[str, Any],
) -> Sequence[str]:
  """Translates all GAE health checks to Cloud Run probe flags.

  Args:
    input_flatten_as_appyaml: A flattened mapping of the input data, with keys
      translated to their app.yaml equivalents.

  Returns:
    A sequence of strings representing the Cloud Run health probe flags.
  """
  return _translate_liveness_check(
      input_flatten_as_appyaml
  ) + _translate_readiness_check(input_flatten_as_appyaml)
