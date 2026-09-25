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
"""Slurm configuration parser utilities for cluster-director CLI."""

from __future__ import annotations

import re
from typing import Any

from googlecloudsdk.command_lib.cluster_director.clusters import errors
from googlecloudsdk.core.util import files


# Supported global Slurm parameters in API (standard camelCase matching proto
# schema).
GLOBAL_SLURM_PARAMS = frozenset([
    'accountingStorageEnforceFlags',
    'accountingStorageTres',
    'additionalSettings',
    'defMemPerCpu',
    'enforcePartLimits',
    'fairShareDampeningFactor',
    'firstJobId',
    'healthCheckInterval',
    'healthCheckNodeState',
    'healthCheckProgram',
    'jobRequeue',
    'overTimeLimit',
    'preemptExemptTime',
    'preemptMode',
    'preemptParameters',
    'preemptType',
    'priorityCalcPeriod',
    'priorityDecayHalfLife',
    'priorityFavorSmall',
    'priorityFlags',
    'priorityMaxAge',
    'priorityType',
    'priorityUsageResetPeriod',
    'priorityWeightAge',
    'priorityWeightAssoc',
    'priorityWeightFairshare',
    'priorityWeightJobSize',
    'priorityWeightPartition',
    'priorityWeightQos',
    'priorityWeightTres',
    'prologEpilogTimeout',
    'prologFlags',
    'requeueExitCodes',
    'requeueHoldExitCodes',
    'schedulerParameters',
    'selectTypeParameters',
])

# Supported sub-parameters for schedulerParameters.
SCHEDULER_PARAMS = frozenset([
    'bfBusyNodes',
    'bfContinue',
    'bfInterval',
    'bfMaxJobPart',
    'bfMaxJobTest',
    'bfMaxJobUser',
    'bfMinAgeReserve',
    'bfResolution',
    'bfWindow',
    'defaultQueueDepth',
    'noholdOnPrologFail',
])

# Supported sub-parameters for preemptParameters.
PREEMPT_PARAMS = frozenset([
    'youngestFirst',
    'strictOrder',
    'reclaimLicenses',
    'sendUserSignal',
    'reorderCount',
    'minExemptPriority',
    'suspendGraceTime',
])

# Supported node-level Slurm parameters.
NODE_SLURM_PARAMS = frozenset([
    'coreSpecCount',
    'cpuSpecList',
    'features',
    'memSpecLimit',
    'weight',
])

# Supported partition-level Slurm parameters.
PARTITION_SLURM_PARAMS = frozenset([
    'allowAccounts',
    'allowQos',
    'defaultTime',
    'defMemPerCpu',
    'denyAccounts',
    'denyQos',
    'exclusiveUser',
    'graceTime',
    'maxNodes',
    'maxTime',
    'overSubscribe',
    'overTimeLimit',
    'preemptMode',
    'priorityJobFactor',
    'priorityTier',
    'qos',
    'tresBillingWeights',
])

# Type definition sets for value coercion.
BOOLEAN_FIELDS = frozenset([
    'bfBusyNodes',
    'bfContinue',
    'noholdOnPrologFail',
    'youngestFirst',
    'strictOrder',
    'reclaimLicenses',
    'sendUserSignal',
])

INTEGER_FIELDS = frozenset([
    'healthCheckInterval',
    'priorityWeightAge',
    'priorityWeightAssoc',
    'priorityWeightFairshare',
    'priorityWeightJobSize',
    'priorityWeightPartition',
    'priorityWeightQos',
])

REPEATED_INT_FIELDS = frozenset([
    'requeueExitCodes',
    'requeueHoldExitCodes',
])

REPEATED_STR_FIELDS = frozenset([
    'prologFlags',
    'accountingStorageEnforceFlags',
    'preemptMode',
])


def _CoerceValue(field_name: str, value: Any) -> Any:
  """Coerces a string value to appropriate type based on field name."""
  if not isinstance(value, str):
    return value

  value_str = value.strip()
  if not value_str:
    return ''

  if field_name in BOOLEAN_FIELDS:
    if value_str.lower() in ('true', '1', 'yes'):
      return True
    if value_str.lower() in ('false', '0', 'no'):
      return False
    raise errors.ClusterDirectorError(
        f'Invalid boolean value {value!r} for field {field_name!r}.'
    )

  if field_name in INTEGER_FIELDS:
    try:
      return int(value_str)
    except ValueError as e:
      raise errors.ClusterDirectorError(
          f'Invalid integer value {value!r} for field {field_name!r}.'
      ) from e

  if field_name in REPEATED_INT_FIELDS:
    delimiter = ':' if ':' in value_str else ','
    parts = [p.strip() for p in value_str.split(delimiter) if p.strip()]
    try:
      return [int(p) for p in parts]
    except ValueError as e:
      raise errors.ClusterDirectorError(
          f'Invalid integer list value {value!r} for field {field_name!r}.'
      ) from e

  if field_name in REPEATED_STR_FIELDS:
    delimiter = ':' if ':' in value_str else ','
    return [p.strip() for p in value_str.split(delimiter) if p.strip()]

  return value_str


def _ParseSubDict(val: Any) -> dict[str, str]:
  """Parses a sub-dict value which may be a dict, JSON string, or '{k=v,k2=v2}'."""
  if isinstance(val, dict):
    return {str(k): str(v) for k, v in val.items()}
  if not isinstance(val, str):
    return {}
  val_str = val.strip()
  if val_str.startswith('{') and val_str.endswith('}'):
    val_str = val_str[1:-1].strip()
  if not val_str:
    return {}
  sub_dict = {}
  tokens = [t.strip() for t in val_str.split(',') if t.strip()]
  for token in tokens:
    if '=' in token:
      k, v = token.split('=', 1)
      sub_dict[k.strip()] = v.strip()
    elif ':' in token:
      k, v = token.split(':', 1)
      sub_dict[k.strip()] = v.strip()
    else:
      sub_dict[token.strip()] = 'true'
  return sub_dict


def ParseSlurmConfigDict(arg_dict: dict[str, Any]) -> dict[str, Any]:
  """Parses and validates an inline ArgDict of Slurm parameters in camelCase.

  Supports dot-notation for nested fields like
  'schedulerParameters.bfBusyNodes=true' and sub-dictionary notation like
  'schedulerParameters="{bfBusyNodes=true,bfInterval=30}"'. Both camelCase and
  snake_case (matching native Slurm parameter names) are supported for nested
  parameters.

  Args:
    arg_dict: Dictionary of key-value pairs from ArgDict.

  Returns:
    Normalized dictionary matching API SlurmConfig structure with camelCase
    keys.

  Raises:
    ClusterDirectorError: If any key is invalid or unrecognized.
  """
  if not arg_dict:
    return {}

  result: dict[str, Any] = {}
  scheduler_params: dict[str, Any] = {}
  preempt_params: dict[str, Any] = {}
  additional_settings: dict[str, Any] = {}

  for raw_key, raw_val in arg_dict.items():
    clean_key = raw_key.strip()
    if '.' in clean_key:
      parent_key, sub_key = clean_key.split('.', 1)
      norm_parent = _SlurmConfKeyToCamelCase(parent_key)
      norm_sub = _SlurmConfKeyToCamelCase(sub_key)
      if norm_parent == 'schedulerParameters':
        if norm_sub not in SCHEDULER_PARAMS:
          raise errors.ClusterDirectorError(
              f'Unrecognized scheduler parameter: {sub_key!r}'
          )
        scheduler_params[norm_sub] = _CoerceValue(norm_sub, raw_val)
      elif norm_parent == 'preemptParameters':
        if norm_sub not in PREEMPT_PARAMS:
          raise errors.ClusterDirectorError(
              f'Unrecognized preempt parameter: {sub_key!r}'
          )
        preempt_params[norm_sub] = _CoerceValue(norm_sub, raw_val)
      elif norm_parent == 'additionalSettings':
        additional_settings[sub_key] = str(raw_val)
      else:
        raise errors.ClusterDirectorError(
            f'Unsupported nested Slurm parameter prefix: {parent_key!r}'
        )
    else:
      norm_key = _SlurmConfKeyToCamelCase(clean_key)
      if norm_key == 'schedulerParameters':
        for sk, sv in _ParseSubDict(raw_val).items():
          norm_sk = _SlurmConfKeyToCamelCase(sk)
          if norm_sk not in SCHEDULER_PARAMS:
            raise errors.ClusterDirectorError(
                f'Unrecognized scheduler parameter: {sk!r}'
            )
          scheduler_params[norm_sk] = _CoerceValue(norm_sk, sv)
      elif norm_key == 'preemptParameters':
        for pk, pv in _ParseSubDict(raw_val).items():
          norm_pk = _SlurmConfKeyToCamelCase(pk)
          if norm_pk not in PREEMPT_PARAMS:
            raise errors.ClusterDirectorError(
                f'Unrecognized preempt parameter: {pk!r}'
            )
          preempt_params[norm_pk] = _CoerceValue(norm_pk, pv)
      elif norm_key == 'additionalSettings':
        additional_settings.update(_ParseSubDict(raw_val))
      elif norm_key in SCHEDULER_PARAMS:
        scheduler_params[norm_key] = _CoerceValue(norm_key, raw_val)
      elif norm_key in PREEMPT_PARAMS:
        preempt_params[norm_key] = _CoerceValue(norm_key, raw_val)
      elif norm_key in GLOBAL_SLURM_PARAMS:
        result[norm_key] = _CoerceValue(norm_key, raw_val)
      else:
        raise errors.ClusterDirectorError(
            f'Unrecognized Slurm configuration parameter: {raw_key!r}'
        )

  if scheduler_params:
    result['schedulerParameters'] = scheduler_params
  if preempt_params:
    result['preemptParameters'] = preempt_params
  if additional_settings:
    result['additionalSettings'] = additional_settings

  return result


SLURM_CONF_KEY_MAP = {
    'accountingstorageenforce': 'accountingStorageEnforceFlags',
    'requeueexit': 'requeueExitCodes',
    'requeueexithold': 'requeueHoldExitCodes',
}


def _SlurmConfKeyToCamelCase(key: str) -> str:
  """Converts native slurm.conf key (e.g. DefMemPerCPU) to camelCase."""
  key_lower = key.lower().replace('_', '')
  if key_lower in SLURM_CONF_KEY_MAP:
    return SLURM_CONF_KEY_MAP[key_lower]
  all_params = (
      GLOBAL_SLURM_PARAMS
      | SCHEDULER_PARAMS
      | PREEMPT_PARAMS
      | NODE_SLURM_PARAMS
      | PARTITION_SLURM_PARAMS
  )
  for param in all_params:
    if param.lower() == key_lower:
      return param
  return key[:1].lower() + key[1:] if key else key


def ExpandSlurmHostlist(hostlist_str: str) -> list[str]:
  """Expands Slurm bracket notation (e.g. 'compute-nodes-[0-3,5,08-10]').

  Args:
    hostlist_str: String containing hostnames or bracketed ranges.

  Returns:
    List of expanded individual hostnames.
  """
  if not hostlist_str:
    return []

  # Split comma-separated items outside of brackets.
  tokens = []
  current = []
  bracket_depth = 0
  for char in hostlist_str:
    if char == '[':
      bracket_depth += 1
      current.append(char)
    elif char == ']':
      if bracket_depth > 0:
        bracket_depth -= 1
      current.append(char)
    elif char == ',' and bracket_depth == 0:
      if current:
        tokens.append(''.join(current).strip())
        current = []
    else:
      current.append(char)
  if current:
    tokens.append(''.join(current).strip())

  expanded_hosts = []
  for token in tokens:
    match = re.search(r'^(.*?)\[(.*?)\](.*)$', token)
    if not match:
      if token:
        expanded_hosts.append(token)
      continue

    prefix, range_body, suffix = match.group(1), match.group(2), match.group(3)
    for part in range_body.split(','):
      part = part.strip()
      if not part:
        continue
      if '-' in part:
        start_str, end_str = part.split('-', 1)
        start_str = start_str.strip()
        end_str = end_str.strip()
        width = (
            len(start_str)
            if start_str.startswith('0') and len(start_str) > 1
            else 0
        )
        try:
          start, end = int(start_str), int(end_str)
          for i in range(start, end + 1):
            formatted_num = f'{i:0{width}d}' if width else str(i)
            expanded_hosts.append(f'{prefix}{formatted_num}{suffix}')
        except ValueError:
          expanded_hosts.append(f'{prefix}{part}{suffix}')
      else:
        expanded_hosts.append(f'{prefix}{part}{suffix}')

  return expanded_hosts


def ParseSlurmConfFile(file_path: str) -> dict[str, Any]:
  """Parses a native slurm.conf configuration file.

  Args:
    file_path: Path to the slurm.conf file.

  Returns:
    Normalized dictionary matching API SlurmOrchestrator structure:
    {
      'config': {...},
      'nodeSets': {...},
      'partitions': {...}
    }

  Raises:
    ClusterDirectorError: If the file is invalid or contains unrecognized
      fields.
  """
  try:
    content = files.ReadFileContents(file_path)
  except Exception as e:
    raise errors.ClusterDirectorError(
        f'Failed to read slurm.conf file [{file_path}]: {e}'
    ) from e

  raw_lines = content.splitlines()
  lines = []
  current_line = ''
  for line in raw_lines:
    stripped = line.strip()
    if stripped.endswith('\\'):
      current_line += stripped[:-1] + ' '
    else:
      current_line += stripped
      if current_line:
        lines.append(current_line)
      current_line = ''
  if current_line:
    lines.append(current_line)

  config_dict: dict[str, Any] = {}
  scheduler_params: dict[str, Any] = {}
  preempt_params: dict[str, Any] = {}
  additional_settings: dict[str, Any] = {}
  node_sets_dict: dict[str, Any] = {}
  partitions_dict: dict[str, Any] = {}

  for line in lines:
    line = line.strip()
    if not line or line.startswith('#'):
      continue
    if '#' in line:
      line = line.split('#', 1)[0].strip()
    if not line:
      continue

    # Check if this line is a NodeName or PartitionName definition
    tokens = line.split()
    first_token = tokens[0] if tokens else ''
    if '=' in first_token:
      k, v = first_token.split('=', 1)
      k_lower = k.lower().replace('_', '')
      if k_lower == 'nodename':
        raw_node_names = v.strip()
        node_names = ExpandSlurmHostlist(raw_node_names)
        node_attrs = {}
        for token in tokens[1:]:
          if '=' in token:
            tk, tv = token.split('=', 1)
            norm_tk = _SlurmConfKeyToCamelCase(tk)
            if norm_tk not in NODE_SLURM_PARAMS:
              raise errors.ClusterDirectorError(
                  f'Unrecognized node parameter in slurm.conf: {tk!r}'
              )
            node_attrs[norm_tk] = _CoerceValue(norm_tk, tv)
        if raw_node_names:
          node_sets_dict[raw_node_names] = node_attrs
        for n_name in node_names:
          if n_name.strip():
            node_sets_dict[n_name.strip()] = node_attrs
        continue
      elif k_lower == 'partitionname':
        part_name = v
        part_attrs = {}
        for token in tokens[1:]:
          if '=' in token:
            tk, tv = token.split('=', 1)
            norm_tk = _SlurmConfKeyToCamelCase(tk)
            if norm_tk not in PARTITION_SLURM_PARAMS:
              raise errors.ClusterDirectorError(
                  f'Unrecognized partition parameter in slurm.conf: {tk!r}'
              )
            part_attrs[norm_tk] = _CoerceValue(norm_tk, tv)
        partitions_dict[part_name] = part_attrs
        continue

    # Global parameter: Key=Value
    if '=' not in line:
      raise errors.ClusterDirectorError(
          f'Invalid line in slurm.conf (missing =): {line!r}'
      )
    key, val = line.split('=', 1)
    key = key.strip()
    val = val.strip()
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
      val = val[1:-1]

    norm_key = _SlurmConfKeyToCamelCase(key)
    if norm_key == 'schedulerParameters':
      sub_parts = val.split(',')
      for sub in sub_parts:
        sub = sub.strip()
        if not sub:
          continue
        if '=' in sub:
          sk, sv = sub.split('=', 1)
        else:
          sk, sv = sub, 'true'
        norm_sk = _SlurmConfKeyToCamelCase(sk)
        if norm_sk not in SCHEDULER_PARAMS:
          raise errors.ClusterDirectorError(
              f'Unrecognized scheduler parameter in slurm.conf: {sk!r}'
          )
        scheduler_params[norm_sk] = _CoerceValue(norm_sk, sv)
    elif norm_key == 'preemptParameters':
      sub_parts = val.split(',')
      for sub in sub_parts:
        sub = sub.strip()
        if not sub:
          continue
        if '=' in sub:
          sk, sv = sub.split('=', 1)
        else:
          sk, sv = sub, 'true'
        norm_sk = _SlurmConfKeyToCamelCase(sk)
        if norm_sk not in PREEMPT_PARAMS:
          raise errors.ClusterDirectorError(
              f'Unrecognized preempt parameter in slurm.conf: {sk!r}'
          )
        preempt_params[norm_sk] = _CoerceValue(norm_sk, sv)
    elif norm_key == 'additionalSettings':
      sub_parts = val.split(',')
      for sub in sub_parts:
        sub = sub.strip()
        if not sub:
          continue
        if '=' in sub:
          ak, av = sub.split('=', 1)
        else:
          ak, av = sub, 'true'
        additional_settings[ak.strip()] = av.strip()
    elif norm_key in GLOBAL_SLURM_PARAMS:
      config_dict[norm_key] = _CoerceValue(norm_key, val)
    else:
      additional_settings[key] = val

  if scheduler_params:
    config_dict['schedulerParameters'] = scheduler_params
  if preempt_params:
    config_dict['preemptParameters'] = preempt_params
  if additional_settings:
    config_dict['additionalSettings'] = additional_settings

  result: dict[str, Any] = {}
  if config_dict:
    result['config'] = config_dict
  if node_sets_dict:
    result['nodeSets'] = node_sets_dict
  if partitions_dict:
    result['partitions'] = partitions_dict
  return result
