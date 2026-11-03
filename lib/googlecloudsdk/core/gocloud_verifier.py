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

"""Verification engine for Go gcloud migration.

This module hydrates a Calliope Namespace from the Go payload (passed via
GOCLOUD_PAYLOAD env var), compares it against the Python parser Namespace,
and reports mismatches.
"""

import os

from googlecloudsdk.calliope import namespace_hydrator
from googlecloudsdk.calliope import namespace_serializer
from googlecloudsdk.core import log
from googlecloudsdk.core.util import encoding

# If this environment variable is '1', a parity mismatch fails the command.
_STRICT_PARITY_ENV = 'GOCLOUD_STRICT_PARITY'


class ParityMismatchError(Exception):
  """Go and Python parsed the arguments of a command differently."""


def IsStrictParity():
  """Returns True if a parity mismatch must fail the command."""
  return encoding.GetEncodedValue(os.environ, _STRICT_PARITY_ENV) == '1'


def Verify(py_namespace, go_payload_json):
  """Compares the Python namespace with the Go namespace from the payload.

  Logs the mismatches at debug level.

  Args:
    py_namespace: The namespace that the Python parser made.
    go_payload_json: str, The GOCLOUD_PAYLOAD JSON that Go sent.

  Raises:
    ParityMismatchError: If there are mismatches and IsStrictParity() is True.
  """
  payload = _ParseGoPayload(go_payload_json)
  if payload is None:
    return

  calliope_command = py_namespace._GetCommand()  # pylint: disable=protected-access
  if getattr(calliope_command, '_parser', None) is None:
    calliope_command._parser = py_namespace._GetParser()  # pylint: disable=protected-access

  py_cmd_path = calliope_command.GetPath()
  go_cmd_path = payload.command_path
  mismatches = []

  # 1. Compare Command Path (Routing)
  _VerifyCommandPath(py_cmd_path, go_cmd_path, mismatches)

  # 2. Hydrate Go Namespace and Compare Namespace-to-Namespace
  go_namespace = namespace_hydrator.HydrateNamespace(calliope_command, payload)

  _VerifySpecifiedArgs(
      list(py_namespace.GetSpecifiedArgNames()),
      list(go_namespace.GetSpecifiedArgNames()),
      mismatches,
  )

  _VerifyNamespaceValues(py_namespace, go_namespace, mismatches)

  if mismatches:
    _ReportMismatches(py_cmd_path, mismatches)
    if IsStrictParity():
      raise ParityMismatchError(
          'GOCLOUD ARG PARITY MISMATCH for command [{}]: {}'.format(
              ' '.join(py_cmd_path), mismatches
          )
      )


def _ParseGoPayload(go_payload_json):
  """Parses GOCLOUD_PAYLOAD JSON string into a namespace_hydrator.Payload."""
  try:
    return namespace_hydrator.Payload.FromJson(go_payload_json)
  except Exception as e:  # pylint: disable=broad-except
    log.debug('Failed to parse GOCLOUD_PAYLOAD JSON: %s', e)
    return None


def _VerifyCommandPath(py_cmd_path, go_cmd_path, mismatches):
  """Compares Python and Go command paths."""
  if go_cmd_path != py_cmd_path:
    mismatches.append({
        'type': 'command_path',
        'expected': py_cmd_path,
        'actual': go_cmd_path,
    })


def _VerifySpecifiedArgs(py_specified, go_specified, mismatches):
  """Compares specified argument lists between Python and Go namespaces."""
  go_spec_norm = set()
  for s in go_specified:
    norm = s.lstrip('-').replace('_', '-').lower()
    if norm.startswith('no-'):
      norm = norm[3:]
    go_spec_norm.add(norm)

  py_spec_norm = set()
  for s in py_specified:
    norm = s.lstrip('-').replace('_', '-')
    if ':' in norm:
      norm = norm.split(':', 1)[0]
    norm = norm.lower()
    if norm.startswith('no-'):
      norm = norm[3:]
    py_spec_norm.add(norm)

  if go_spec_norm != py_spec_norm:
    mismatches.append({
        'type': 'specified_args',
        'expected': sorted(list(py_spec_norm)),
        'actual': sorted(list(go_spec_norm)),
    })


def _VerifyNamespaceValues(py_namespace, go_namespace, mismatches):
  """Compares normalized attribute values between Python and Go namespaces."""
  raw_diffs = namespace_serializer.CompareArgs(
      py_namespace, go_namespace, ignore_empty=True
  )
  if raw_diffs:
    arg_mismatches = {
        k.rstrip('_')
        .replace('_', '-')
        .lower(): {
            'expected': diff['expected'],
            'actual': diff['actual'],
        }
        for k, diff in raw_diffs.items()
    }
    mismatches.append({'type': 'arguments', 'mismatches': arg_mismatches})


def _ReportMismatches(cmd_path, mismatches):
  """Logs warnings for all recorded mismatches."""
  cmd_str = ' '.join(cmd_path)
  log.debug('Go gcloud verification mismatch for command: %s', cmd_str)
  for m in mismatches:
    if m['type'] == 'arguments':
      for arg, diff in m['mismatches'].items():
        log.debug(
            '  Arg [%s] mismatch: Python=%s, Go=%s',
            arg,
            diff['expected'],
            diff['actual'],
        )
    else:
      log.debug(
          '  Mismatch [%s]: Python=%s, Go=%s',
          m['type'],
          m['expected'],
          m['actual'],
      )
