# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Flags for data-catalog commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def AddPrivatecloudArgToParser(parser, positional=False):
  """Sets up an argument for the privatecloud resource."""
  name = '--private-cloud'
  if positional:
    name = 'private_cloud'
  privatecloud_data = yaml_data.ResourceYAMLData.FromPath(
      'vmware.private_cloud')
  resource_spec = concepts.ResourceSpec.FromYaml(privatecloud_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='private_cloud.'
      )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddOperationArgToParser(parser):
  """Sets up an argument for the operation resource."""
  operation_data = yaml_data.ResourceYAMLData.FromPath('vmware.operation')
  resource_spec = concepts.ResourceSpec.FromYaml(operation_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='operation',
      concept_spec=resource_spec,
      required=True,
      group_help='operation.'
      )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddSubnetArgToParser(parser):
  """Sets up an argument for the subnet resource."""

  address_data = yaml_data.ResourceYAMLData.FromPath('vmware.subnet')
  resource_spec = concepts.ResourceSpec.FromYaml(address_data.GetData())

  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='subnet',
      concept_spec=resource_spec,
      required=True,
      group_help='subnet.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddClusterArgToParser(parser, positional=False):
  """Sets up an argument for the cluster resource."""
  if positional:
    name = 'cluster'
  else:
    name = '--cluster'
  cluster_data = yaml_data.ResourceYAMLData.FromPath('vmware.cluster')
  resource_spec = concepts.ResourceSpec.FromYaml(cluster_data.GetData())
  flag_name_overrides = {'location': '', 'private-cloud': ''}

  if positional:
    flag_name_overrides = None
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='cluster.',
      flag_name_overrides=flag_name_overrides
      )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddExternalAddressArgToParser(parser):
  """Sets up an argument for the external address resource."""

  address_data = yaml_data.ResourceYAMLData.FromPath('vmware.external_address')
  resource_spec = concepts.ResourceSpec.FromYaml(address_data.GetData())

  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='external_address',
      concept_spec=resource_spec,
      required=True,
      group_help='external_address.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddManagementDnsZoneBindingArgToParser(parser):
  """Sets up an argument for the management DNS zone binding resource."""

  path = 'vmware.management_dns_zone_binding'
  address_data = yaml_data.ResourceYAMLData.FromPath(path)
  resource_spec = concepts.ResourceSpec.FromYaml(address_data.GetData())

  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='management_dns_zone_binding',
      concept_spec=resource_spec,
      required=True,
      group_help='management_dns_zone_binding.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddHcxActivationKeyArgToParser(parser):
  """Sets up an argument for the HCX activation key resource."""
  hcx_activation_key_data = yaml_data.ResourceYAMLData.FromPath(
      'vmware.hcx_activation_key')
  resource_spec = concepts.ResourceSpec.FromYaml(
      hcx_activation_key_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='hcx_activation_key',
      concept_spec=resource_spec,
      required=True,
      group_help='hcxactivationkey.',
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddLocationArgToParser(parser, regional=False, positional=False):
  """Parses location flag."""
  location_data = yaml_data.ResourceYAMLData.FromPath('vmware.location')
  if regional:
    location_data = yaml_data.ResourceYAMLData.FromPath(
        'vmware.regional_location')
  resource_spec = concepts.ResourceSpec.FromYaml(location_data.GetData())
  name = '--location'
  if positional:
    name = 'location'
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='location.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddNodeTypeArgToParser(parser, positional=False):
  """Parses node type flag."""

  if positional:
    name = 'node_type'
    flag_name_overrides = None
  else:
    name = '--node-type'
    flag_name_overrides = {'location': ''}

  location_data = yaml_data.ResourceYAMLData.FromPath('vmware.node_type')
  resource_spec = concepts.ResourceSpec.FromYaml(location_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='node_type.',
      flag_name_overrides=flag_name_overrides)
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddProjectArgToParser(parser, positional=False):
  """Parses project flag."""
  name = '--project'
  if positional:
    name = 'project'

  project_data = yaml_data.ResourceYAMLData.FromPath('vmware.project')
  resource_spec = concepts.ResourceSpec.FromYaml(project_data.GetData())

  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='project.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddPrivateConnectionToParser(parser, positional=False):
  """Sets up an argument for the Private Connection resource."""
  name = '--private-connection'
  if positional:
    name = 'private_connection'
  private_connection_data = yaml_data.ResourceYAMLData.FromPath(
      'vmware.private_connection')
  resource_spec = concepts.ResourceSpec.FromYaml(
      private_connection_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='private_connection.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)
