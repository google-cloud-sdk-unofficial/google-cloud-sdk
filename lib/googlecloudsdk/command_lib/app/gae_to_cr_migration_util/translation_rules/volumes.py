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

"""Translation rule for app resources (volumes)."""

from collections.abc import Mapping, Sequence
from typing import Any
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.common import util


def translate_volumes(input_data: Mapping[str, Any]) -> Sequence[str]:
  """Translates resources.volumes to Cloud Run --add-volume flags.

  Args:
    input_data: Flattened dictionary of the input data from app.yaml.

  Returns:
    List of output flags.
  """
  if not util.is_flex_env(input_data):
    return []

  volumes = input_data.get('resources.volumes')
  if not volumes:
    return []

  flags = []
  for volume in volumes:
    name = volume.get('name')
    if not name:
      continue
    volume_type = volume.get('volume_type')
    size_gb = volume.get('size_gb')

    if volume_type == 'tmpfs':
      # Cloud Run in-memory volumes use size-limit in Mi or Gi.
      # Flex uses size_gb in float. 1GB = 1024Mi.
      size_mi = int(float(size_gb) * 1024) if size_gb else 512
      flags.append(
          f'--add-volume=name={name},type=in-memory,size-limit={size_mi}Mi'
      )
      flags.append(f'--add-volume-mount=volume={name},mount-path=/mnt/{name}')

  return flags
