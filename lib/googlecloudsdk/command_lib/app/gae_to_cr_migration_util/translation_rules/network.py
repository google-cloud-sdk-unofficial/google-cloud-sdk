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
import json
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


def update_service_yaml_with_network(
    service_yaml: dict[str, Any],
    input_data: Mapping[str, Any],
) -> None:
  """Update the service_yaml dict with networking settings.

  Args:
    service_yaml: The dictionary representation of the Cloud Run service YAML to
      be updated.
    input_data: Flattened dictionary of the parsed app.yaml file, containing
      networking configurations.
  """

  # 1. Service level annotations
  service_metadata = service_yaml.setdefault('metadata', {})
  service_annotations = service_metadata.setdefault('annotations', {})

  instance_ip_mode = input_data.get(
      'network.instance_ip_mode'
  ) or input_data.get('network.instanceIpMode')
  if instance_ip_mode == 'external':
    service_annotations['run.googleapis.com/ingress'] = 'all'
  elif instance_ip_mode == 'internal':
    service_annotations['run.googleapis.com/ingress'] = 'internal'

  # 2. Revision level metadata & annotations
  spec = service_yaml.setdefault('spec', {})
  template = spec.setdefault('template', {})
  template_metadata = template.setdefault('metadata', {})
  template_annotations = template_metadata.setdefault('annotations', {})

  if input_data.get('network.session_affinity'):
    template_annotations['run.googleapis.com/sessionAffinity'] = 'true'

  # 3. Direct VPC (Network, Subnet, and Tags)
  network_interface = {}
  if network_name := input_data.get('network.name'):
    network_interface['network'] = network_name
  if subnetwork_name := input_data.get('network.subnetwork_name'):
    network_interface['subnetwork'] = subnetwork_name
  if tag_data := input_data.get('network.instance_tag'):
    network_interface['tags'] = (
        tag_data if isinstance(tag_data, list) else [tag_data]
    )

  if network_interface:
    template_annotations['run.googleapis.com/network-interfaces'] = json.dumps(
        [network_interface]
    )

  vpc_connector = input_data.get('vpc_access_connector.name') or input_data.get(
      'vpcAccessConnector.name'
  )
  if vpc_connector:
    template_annotations['run.googleapis.com/vpc-access-connector'] = (
        vpc_connector
    )

  vpc_egress = input_data.get(
      'vpc_access_connector.egress_setting'
  ) or input_data.get('vpcAccessConnector.egressSetting')
  if vpc_egress:
    template_annotations['run.googleapis.com/vpc-access-egress'] = vpc_egress

  # 4. Container level settings
  template_spec = template.setdefault('spec', {})
  containers = template_spec.setdefault('containers', [{}])
  container = containers[0]

  forwarded_ports = input_data.get('network.forwarded_ports') or input_data.get(
      'network.forwardedPorts'
  )
  if forwarded_ports:
    container_ports = container.setdefault('ports', [])
    container_ports.append({'containerPort': int(forwarded_ports[0])})
