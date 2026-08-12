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

This module compares the parsed argument state from the Go wrapper (passed via
GOCLOUD_ARGS env var) with the Python parser output, and reports mismatches.
"""

import datetime
import functools
import json

from googlecloudsdk.core import log


# ==============================================================================
# 1. Extensible Normalization using singledispatch
# ==============================================================================

_TYPE_NAME_NORMALIZERS = {}


def RegisterTypeNameNormalizer(type_name):
  """Decorator to register a normalizer function for a type name string."""
  def _Decorator(func):
    _TYPE_NAME_NORMALIZERS[type_name] = func
    return func
  return _Decorator


def _GetFullTypeName(obj):
  cls = type(obj)
  module = getattr(cls, '__module__', '')
  qualname = getattr(cls, '__qualname__', cls.__name__)
  if module and module != 'builtins':
    return '{}.{}'.format(module, qualname)
  return qualname


@functools.singledispatch
def _NormalizeValue(obj):
  """Default fallback for custom/unknown types."""
  full_name = _GetFullTypeName(obj)
  if full_name in _TYPE_NAME_NORMALIZERS:
    return _TYPE_NAME_NORMALIZERS[full_name](obj)

  return str(obj)


@RegisterTypeNameNormalizer('googlecloudsdk.calliope.arg_parsers.HostPort')
def _NormalizeHostPort(obj):
  host = getattr(obj, 'host', None)
  port = getattr(obj, 'port', None)
  if host is not None and port is not None:
    return '{}:{}'.format(host, port)
  elif host is not None:
    return str(host)
  elif port is not None:
    return ':{}'.format(port)
  return ''


# Register standard types
@_NormalizeValue.register(str)
@_NormalizeValue.register(int)
@_NormalizeValue.register(float)
@_NormalizeValue.register(bool)
@_NormalizeValue.register(type(None))
def _(obj):
  return obj


@_NormalizeValue.register(dict)
def _(obj):
  return {str(k): _NormalizeValue(v) for k, v in obj.items()}


@_NormalizeValue.register(list)
@_NormalizeValue.register(tuple)
def _(obj):
  return [_NormalizeValue(v) for v in obj]


@_NormalizeValue.register(set)
def _(obj):
  try:
    return sorted([_NormalizeValue(v) for v in obj])
  except TypeError:
    return [_NormalizeValue(v) for v in obj]


@_NormalizeValue.register(datetime.datetime)
def _(obj):
  return obj.isoformat()


@_NormalizeValue.register(datetime.timedelta)
def _(obj):
  return obj.total_seconds()


# Compatibility-safe Pattern registration
@RegisterTypeNameNormalizer('re.Pattern')
def _NormalizePattern(obj):
  return obj.pattern


def _NormalizePythonArgs(py_namespace):
  """Extracts and normalizes arguments from Python Namespace."""
  args_dict = {}
  for k, v in vars(py_namespace).items():
    if not k.startswith('_'):
      norm_key = k.rstrip('_').replace('_', '-').lower()
      args_dict[norm_key] = _NormalizeValue(v)
  return args_dict


# ==============================================================================
# 2. Decomposed Verify Pipeline
# ==============================================================================


def Verify(py_namespace, go_args_json):
  """Compares Python namespace with Go parsed args JSON and logs mismatches."""
  go_data = _ParseGoJson(go_args_json)
  if not go_data:
    return

  py_data = _ExtractPythonData(py_namespace)
  mismatches = []

  # 1. Compare Command Path (Routing)
  _VerifyCommandPath(py_data['cmd_path'], go_data['cmd_path'], mismatches)

  # 2. Compare Specified Args
  _VerifySpecifiedArgs(py_data['specified'], go_data['specified'], mismatches)

  # 3. Compare Argument Values
  _VerifyArgumentValues(
      py_data['args'], go_data['resolved'], py_namespace, mismatches
  )

  if mismatches:
    _ReportMismatches(py_data['cmd_path'], mismatches)


def _ParseGoJson(go_args_json):
  """Parses GOCLOUD_ARGS JSON string into a structured dictionary."""
  try:
    go_data = json.loads(go_args_json)
    flags = go_data.get('flags', [])
    args = go_data.get('args', [])
    # Backward compatibility if legacy 'resolved' field is provided
    if 'resolved' in go_data and not flags and not args:
      flags = go_data.get('resolved', [])

    all_resolved = flags + args
    go_specified = [
        item.get('name') for item in all_resolved if item.get('is_set')
    ]
    return {
        'cmd_path': go_data.get('command_path', []),
        'flags': flags,
        'args': args,
        'resolved': all_resolved,
        'specified': go_specified,
    }
  except Exception as e:  # pylint: disable=broad-except
    log.debug('Failed to parse GOCLOUD_ARGS JSON: %s', e)
    return None


def _ExtractPythonData(py_namespace):
  """Extracts parsed arguments and command path from Python namespace."""
  calliope_command = py_namespace._GetCommand()  # pylint: disable=protected-access
  return {
      'cmd_path': calliope_command.GetPath(),
      'args': _NormalizePythonArgs(py_namespace),
      'specified': list(py_namespace.GetSpecifiedArgNames()),
  }


def _VerifyCommandPath(py_cmd_path, go_cmd_path, mismatches):
  """Compares Python and Go command paths."""
  if go_cmd_path != py_cmd_path:
    mismatches.append({
        'type': 'command_path',
        'expected': py_cmd_path,
        'actual': go_cmd_path,
    })


def _VerifySpecifiedArgs(py_specified, go_specified, mismatches):
  """Compares specified argument lists between Python and Go."""
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


def _VerifyArgumentValues(py_args_norm, go_resolved, py_namespace, mismatches):
  """Compares normalized argument values between Python and Go."""
  go_args = {}
  for item in go_resolved:
    name = item.get('name')
    if name:
      go_args[name] = item.get('value')

  go_args_norm = {k.replace('_', '-').lower(): v for k, v in go_args.items()}

  # Get action mapping for property fallback checks
  parser = py_namespace._GetParser()  # pylint: disable=protected-access
  norm_dest_to_action = {}
  if parser:
    for action in parser._actions:  # pylint: disable=protected-access
      if action.dest:
        norm_dest = action.dest.rstrip('_').replace('_', '-').lower()
        if (
            hasattr(action, 'store_property')
            or norm_dest not in norm_dest_to_action
        ):
          norm_dest_to_action[norm_dest] = action

  all_keys = set(go_args_norm.keys()) | set(py_args_norm.keys())
  arg_mismatches = {}
  for k in all_keys:
    go_val = go_args_norm.get(k)
    py_val = py_args_norm.get(k)

    # Property fallback matching
    if py_val is None:
      action = norm_dest_to_action.get(k)
      if action and hasattr(action, 'store_property'):
        prop = action.store_property[0]
        try:
          resolved_py_val = prop.Get()
          if resolved_py_val is not None:
            py_val = _NormalizeValue(resolved_py_val)
        except Exception:  # pylint: disable=broad-except
          pass

    if go_val != py_val:
      if _IsEmpty(go_val) and _IsEmpty(py_val):
        continue
      arg_mismatches[k] = {'expected': py_val, 'actual': go_val}

  if arg_mismatches:
    mismatches.append({
        'type': 'arguments',
        'mismatches': arg_mismatches
    })


def _IsEmpty(val):
  """Returns True if value is None or empty sequence/dict."""
  if val is None:
    return True
  if isinstance(val, (str, list, tuple, dict)) and not val:
    return True
  return False


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
