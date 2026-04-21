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

"""Translation rule for networking features."""

from collections.abc import Mapping, Sequence
from typing import Any


def translate_network_features(
    input_data: Mapping[str, Any],
) -> Sequence[str]:
  """Translate networking features.

  Args:
    input_data: Flattened dictionary of the parsed app.yaml file.

  Returns:
    A list of strings representing the flags for Cloud Run.
  """
  output_flags = []
  if 'network.name' in input_data:
    output_flags.append(f'--network={input_data["network.name"]}')
  if 'network.subnetwork_name' in input_data:
    output_flags.append(f'--subnet={input_data["network.subnetwork_name"]}')
  if 'network.instance_tag' in input_data:
    output_flags.append(f'--network-tags={input_data["network.instance_tag"]}')
  if input_data.get('network.session_affinity'):
    output_flags.append('--session-affinity')

  forwarded_ports = input_data.get('network.forwarded_ports') or input_data.get(
      'network.forwardedPorts'
  )
  if forwarded_ports:
    output_flags.append(f'--port={forwarded_ports[0]}')

  instance_ip_mode = input_data.get(
      'network.instance_ip_mode'
  ) or input_data.get('network.instanceIpMode')
  if instance_ip_mode:
    if instance_ip_mode == 'external':
      output_flags.append('--ingress=all')
    elif instance_ip_mode == 'internal':
      output_flags.append('--ingress=internal')

  return output_flags
