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

"""Translation rule for timeout feature."""

from typing import Any, Mapping, Sequence
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.common import util
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.translation_rules import scaling

_SCALING_METHOD_W_10_MIN_TIMEOUT = frozenset(
    {scaling.ScalingTypeAppYaml.AUTOMATIC_SCALING}
)
_SCALING_METHOD_W_60_MIN_TIMEOUT = frozenset({
    scaling.ScalingTypeAppYaml.MANUAL_SCALING,
    scaling.ScalingTypeAppYaml.BASIC_SCALING,
})

_AUTOMATIC_SCALING_TIMEOUT_SEC = 600
_MANUAL_SCALING_TIMEOUT_SEC = 3600
_FLEX_TIMEOUT_SEC = 3600
_FLEX_TIMEOUT_STR = '60m'


def translate_timeout_features(input_data: Mapping[str, Any]) -> Sequence[str]:
  """Translate timeout features based on scaling method."""
  is_flex = util.is_flex_env(input_data)
  # Flex environment has a default timeout of 60 minutes.
  if is_flex:
    return [f'--timeout={_FLEX_TIMEOUT_STR}']

  scaling_features_used = scaling.get_scaling_features_used(input_data)
  if len(scaling_features_used) == 1:
    scaling_feature = scaling_features_used[0]
    if scaling_feature in _SCALING_METHOD_W_10_MIN_TIMEOUT:
      return [f'--timeout={_AUTOMATIC_SCALING_TIMEOUT_SEC}']
    if scaling_feature in _SCALING_METHOD_W_60_MIN_TIMEOUT:
      return [f'--timeout={_MANUAL_SCALING_TIMEOUT_SEC}']
  return []


def update_service_yaml_with_timeout(
    service_yaml: dict[str, Any],
    input_data: Mapping[str, Any],
) -> None:
  """Updates the service_yaml dict with timeout settings."""
  is_flex = util.is_flex_env(input_data)
  timeout_val = None
  if is_flex:
    timeout_val = _FLEX_TIMEOUT_SEC
  else:
    scaling_features_used = scaling.get_scaling_features_used(input_data)
    if len(scaling_features_used) == 1:
      scaling_feature = scaling_features_used[0]
      if scaling_feature in _SCALING_METHOD_W_10_MIN_TIMEOUT:
        timeout_val = _AUTOMATIC_SCALING_TIMEOUT_SEC
      elif scaling_feature in _SCALING_METHOD_W_60_MIN_TIMEOUT:
        timeout_val = _MANUAL_SCALING_TIMEOUT_SEC

  if timeout_val:
    spec = service_yaml.setdefault('spec', {})
    template = spec.setdefault('template', {})
    template_spec = template.setdefault('spec', {})
    template_spec['timeoutSeconds'] = timeout_val
    service_yaml['spec']['template']['spec']['timeoutSeconds'] = timeout_val
