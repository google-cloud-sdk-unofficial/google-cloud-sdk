# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Translation rule for app resources (instance_class, cpu, memory)."""

import logging
import math
from typing import Mapping, Sequence, Tuple
import frozendict
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.common import util
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.translation_rules import scaling


_ALLOWED_RESOURCE_KEY = tuple(['resources.cpu', 'resources.memory_gb'])
_DEFAULT_CPU = 1
_DEFAULT_MEMORY = 0.6
_ALLOW_INSTANCE_CLASS_KEY = 'instance_class'
_DEFAULT_CPU_MEM_CONFIG = frozendict.frozendict({
    scaling.ScalingTypeAppYaml.AUTOMATIC_SCALING: 'F1',
    scaling.ScalingTypeAppYaml.MANUAL_SCALING: 'B2',
    scaling.ScalingTypeAppYaml.BASIC_SCALING: 'B2',
})
# See https://cloud.google.com/run/docs/configuring/cpu
# See https://cloud.google.com/run/docs/configuring/memory-limits
_INSTANCE_CLASS_MAP = frozendict.frozendict({
    'F1': {'cpu': 1, 'memory': 0.25},
    'F2': {'cpu': 1, 'memory': 0.5},
    'F4': {'cpu': 1, 'memory': 1},
    'F4_1G': {'cpu': 1, 'memory': 2},
    'B1': {'cpu': 1, 'memory': 0.25},
    'B2': {'cpu': 1, 'memory': 0.5},
    'B4': {'cpu': 1, 'memory': 1},
    'B4_1G': {'cpu': 1, 'memory': 2},
    'B8': {'cpu': 2, 'memory': 2},
})


def translate_app_resources(
    input_data: Mapping[str, any]
) -> Sequence[str]:
  """Translate instance_class(standard) to equivalent/compatible.

  Cloud Run --cpu and --memory flags.

  Args:
    input_data: Dictionary of the input data from app.yaml.

  Returns:
    List of output flags.
  """
  if util.is_flex_env(input_data):
    return _translate_flex_cpu_memory(input_data)
  return _translate_standard_instance_class(input_data)


def _translate_flex_cpu_memory(input_data: Mapping[str, any]) -> Sequence[str]:
  """Translate flex cpu/memory to equivalent/compatible Cloud Run flags.

  Args:
    input_data: Dictionary of the input data from app.yaml.

  Returns:
    List of output flags.
  """

  cpu = float(input_data.get('resources.cpu') or _DEFAULT_CPU)
  memory = float(input_data.get('resources.memory_gb') or _DEFAULT_MEMORY)
  cpu, memory = _convert_cpu_memory(cpu, memory)
  return _generate_flags(cpu_value=cpu, memory_value=memory)


def _translate_standard_instance_class(
    input_data: Mapping[str, any]
) -> Sequence[str]:
  """Translate standard instance_class to equivalent/compatible Cloud Run flags.

  Args:
    input_data: Dictionary of the input data from app.yaml.

  Returns:
    List of output flags.
  """
  instance_class_key_from_input = util.get_feature_key_from_input(
      input_data, [_ALLOW_INSTANCE_CLASS_KEY]
  )
  if instance_class_key_from_input:
    instance_class = input_data[instance_class_key_from_input]
    return _generate_cpu_memory_flags_by_instance_class(instance_class)
  return _get_cpu_memory_default_based_on_scaling_method(input_data)


def _get_cpu_memory_default_based_on_scaling_method(
    input_data: Mapping[str, any]
) -> Sequence[str]:
  """Get default cpu/memory based on scaling method.

  Args:
    input_data: Dictionary of the input data from app.yaml.

  Returns:
    List of output flags.
  """
  scaling_features_used = scaling.get_scaling_features_used(input_data)
  if not scaling_features_used:
    return []
  if len(scaling_features_used) > 1:
    logging.warning(
        'Warning: More than one scaling option is defined, only one'
        ' scaling option should be used.'
    )
    return []
  scaling_method = scaling_features_used[0]
  default_instance_class = _DEFAULT_CPU_MEM_CONFIG[scaling_method]
  return _generate_cpu_memory_flags_by_instance_class(default_instance_class)


def _generate_flags(*, cpu_value: float, memory_value: float) -> Sequence[str]:
  """Generate cpu/memory flags based on cpu/memory values.

  Args:
    cpu_value: CPU value in float.
    memory_value: Memory value in GiB as float.

  Returns:
    List of output flags.
  """

  # Cloud Run --memory requires a unit suffix
  # https://cloud.google.com/run/docs/configuring/memory-limits#setting-services
  return [
      f'--cpu={cpu_value}',
      f'--memory={_format_cloud_run_memory_unit(memory_value)}',
  ]


def _generate_cpu_memory_flags_by_instance_class(
    instance_class: str,
) -> Sequence[str]:
  """Generate cpu/memory flags based on instance class.

  Args:
    instance_class: Instance class string.

  Returns:
    List of output flags.
  """
  instance_config = _INSTANCE_CLASS_MAP[instance_class]
  cpu_value = instance_config['cpu']
  memory_value = instance_config['memory']
  cpu_value, memory_value = _convert_cpu_memory(cpu_value, memory_value)
  return _generate_flags(cpu_value=cpu_value, memory_value=memory_value)


def _adjust_cpu_for_mem(cpu_value: float, clamped_memory: float) -> float:
  """Adjust CPU based on Memory Requirements.

  Args:
    cpu_value: CPU value in float.
    clamped_memory: Memory value in GiB as float, clamped to [0.5, 32].

  Returns:
    CPU value after memory adjustment.
  """
  if clamped_memory > 24:
    cpu_after_mem_adjust = max(cpu_value, 8)
  elif clamped_memory > 16:
    cpu_after_mem_adjust = max(cpu_value, 6)
  elif clamped_memory > 8:
    cpu_after_mem_adjust = max(cpu_value, 4)
  elif clamped_memory > 4:
    cpu_after_mem_adjust = max(cpu_value, 2)
  elif clamped_memory > 1:
    cpu_after_mem_adjust = max(cpu_value, 1)
  elif clamped_memory > 0.5:
    cpu_after_mem_adjust = max(cpu_value, 0.5)
  else:
    cpu_after_mem_adjust = max(cpu_value, 0.08)
  return cpu_after_mem_adjust


def _adjust_mem_for_cpu(
    cpu_after_mem_adjust: float, clamped_memory: float
) -> float:
  """Adjust Memory based on CPU Requirements.

  Args:
    cpu_after_mem_adjust: CPU value after memory adjustment.
    clamped_memory: Memory value in GiB as float, clamped to [0.5, 32].

  Returns:
    Memory value after CPU adjustment.
  """
  # 4 vCPU: 2 to 16 GiB
  # 6 vCPU: 4 to 24 GiB
  # 8 vCPU: 4 to 32 GiB
  if cpu_after_mem_adjust >= 6:
    memory_after_cpu_adjust = max(clamped_memory, 4)
  elif cpu_after_mem_adjust >= 4:
    memory_after_cpu_adjust = max(clamped_memory, 2)
  else:
    memory_after_cpu_adjust = clamped_memory
  return memory_after_cpu_adjust


def _do_final_cpu_and_mem_adjustments(
    cpu_after_mem_adjust: float, memory_after_cpu_adjust: float
) -> Tuple[float, float]:
  """Do final CPU and Memory adjustments.

  Args:
    cpu_after_mem_adjust: CPU value after memory adjustment.
    memory_after_cpu_adjust: Memory value after CPU adjustment.

  Returns:
    Tuple of (cpu, memory) values, where memory is in GiB.
  """
  # Final CPU constraints
  if cpu_after_mem_adjust > 1:
    temp_cpu = int(math.ceil(cpu_after_mem_adjust))
    final_cpu = min(temp_cpu, 8)
  elif cpu_after_mem_adjust < 0.08:
    final_cpu = 0.08
  else:
    temp_cpu = round(cpu_after_mem_adjust, 3)
    final_cpu = int(temp_cpu) if temp_cpu == int(temp_cpu) else temp_cpu

  if memory_after_cpu_adjust == int(memory_after_cpu_adjust):
    final_memory = int(memory_after_cpu_adjust)
  else:
    final_memory = memory_after_cpu_adjust

  return final_cpu, final_memory


def _convert_cpu_memory(
    cpu_value: float, memory_value: float
) -> Tuple[float, float]:
  """Convert cpu/memory to equivalent/compatible Cloud Run values.

  Args:
    cpu_value: CPU value in float.
    memory_value: Memory value in GiB as float.

  Returns:
    Tuple of (cpu, memory) values, where memory is in GiB.
  """
  # https://docs.cloud.google.com/run/docs/configuring/services/cpu#setting

  # Ensure memory is within [0.5, 32] GiB
  clamped_memory = min(max(memory_value, 0.5), 32)

  cpu_after_mem_adjust = _adjust_cpu_for_mem(cpu_value, clamped_memory)
  memory_after_cpu_adjust = _adjust_mem_for_cpu(
      cpu_after_mem_adjust, clamped_memory
  )

  return _do_final_cpu_and_mem_adjustments(
      cpu_after_mem_adjust, memory_after_cpu_adjust
  )


def _format_cloud_run_memory_unit(value: float) -> str:
  """Format memory value with Cloud Run unit.

  Args:
    value: Memory value in float.

  Returns:
    Memory value with Cloud Run unit.
  """
  # 1GB = 953Mi, 1Gi = 1024Mi memory, in Cloud Run, a minimum of 512MiB memory
  # is required for 1 CPU. Therefore, using Gi works for the lower bound of
  # memory requirement.
  # Allowed values are [m, k, M, G, T, Ki, Mi, Gi, Ti, Pi, Ei]
  return f'{value}Gi'
