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

from typing import Any

from googlecloudsdk.command_lib.cluster_director.clusters import errors


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


def ParseSlurmConfigDict(arg_dict: dict[str, Any]) -> dict[str, Any]:
  """Parses and validates an inline ArgDict of Slurm parameters in camelCase.

  Supports dot-notation for nested fields like
  'schedulerParameters.bfBusyNodes=true'.

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

  for raw_key, raw_val in arg_dict.items():
    clean_key = raw_key.strip()
    if '.' in clean_key:
      parent_key, sub_key = clean_key.split('.', 1)
      if parent_key == 'schedulerParameters':
        if sub_key not in SCHEDULER_PARAMS:
          raise errors.ClusterDirectorError(
              f'Unrecognized scheduler parameter: {sub_key!r}'
          )
        scheduler_params[sub_key] = _CoerceValue(sub_key, raw_val)
      elif parent_key == 'preemptParameters':
        if sub_key not in PREEMPT_PARAMS:
          raise errors.ClusterDirectorError(
              f'Unrecognized preempt parameter: {sub_key!r}'
          )
        preempt_params[sub_key] = _CoerceValue(sub_key, raw_val)
      else:
        raise errors.ClusterDirectorError(
            f'Unsupported nested Slurm parameter prefix: {parent_key!r}'
        )
    else:
      if clean_key in SCHEDULER_PARAMS:
        scheduler_params[clean_key] = _CoerceValue(clean_key, raw_val)
      elif clean_key in PREEMPT_PARAMS:
        preempt_params[clean_key] = _CoerceValue(clean_key, raw_val)
      elif clean_key in GLOBAL_SLURM_PARAMS:
        result[clean_key] = _CoerceValue(clean_key, raw_val)
      else:
        raise errors.ClusterDirectorError(
            f'Unrecognized Slurm configuration parameter: {raw_key!r}'
        )

  if scheduler_params:
    result['schedulerParameters'] = scheduler_params
  if preempt_params:
    result['preemptParameters'] = preempt_params

  return result

