# -*- coding: utf-8 -*- #
# Copyright 2023 Google Inc. All Rights Reserved.
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
"""services policies test-enabled command."""
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_PROJECT_RESOURCE = 'projects/%s'
_FOLDER_RESOURCE = 'folders/%s'
_ORGANIZATION_RESOURCE = 'organizations/%s'
_SERVICE = 'services/%s'


def _GetContainers(policies):
  """Extracts container names from policy resource strings."""
  containers = []
  for p in policies:
    container = p.split('/consumerPolicies/')[0]
    if container not in containers:
      containers.append(container)
  return containers


def _FormatTestEnabledResponse(
    response, service_name, resource_name, is_catalog
):
  """Formats test-enabled response with multi-level enablement details."""
  if is_catalog:
    if response.enableRules:
      containers = []
      for metadata in response.enableRuleMetadata or []:
        if (
            metadata.catalogSources
            and metadata.catalogSources.additionalProperties
        ):
          for prop in metadata.catalogSources.additionalProperties:
            if (
                prop.key == service_name
                or f'catalogs/{prop.key}' == service_name
            ):
              for c in _GetContainers(prop.value.policies):
                if c not in containers:
                  containers.append(c)
      if containers:
        return (
            f'Catalog {service_name} is ENABLED from'
            f' {", ".join(containers)}.'
        )
      return f'Catalog {service_name} is ENABLED for resource {resource_name}.'
    else:
      return (
          f'Catalog {service_name} is NOT ENABLED for resource'
          f' {resource_name}.'
      )

  # If enableRules is empty that means service is not enabled.
  if not response.enableRules:
    return (
        f'Service {service_name} is NOT ENABLED for resource {resource_name}.'
    )

  direct_containers = []
  catalog_containers_map = {}

  for metadata in response.enableRuleMetadata or []:
    if metadata.serviceSources and metadata.serviceSources.additionalProperties:
      for prop in metadata.serviceSources.additionalProperties:
        for c in _GetContainers(prop.value.policies):
          if c not in direct_containers:
            direct_containers.append(c)
    if metadata.catalogSources and metadata.catalogSources.additionalProperties:
      for prop in metadata.catalogSources.additionalProperties:
        catalog_name = prop.key
        if catalog_name not in catalog_containers_map:
          catalog_containers_map[catalog_name] = []
        for c in _GetContainers(prop.value.policies):
          if c not in catalog_containers_map[catalog_name]:
            catalog_containers_map[catalog_name].append(c)

  lines = []
  if direct_containers:
    lines.append(
        f'Service {service_name} is ENABLED from'
        f' {", ".join(direct_containers)}.'
    )

  for cat, containers in catalog_containers_map.items():
    if containers:
      lines.append(
          f'Service {service_name} is ENABLED via {cat} from'
          f' {", ".join(containers)}.'
      )

  return '\n'.join(lines)


def _ParseServiceArg(service: str):
  """Returns a tuple of (service_arg, is_catalog)."""
  is_catalog = service.startswith('catalogs/')
  if is_catalog or service.startswith('services/'):
    return service, is_catalog
  return _SERVICE % service, False


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class TestEnabledBeta(base.Command):
  """Test a value against the result of merging consumer policies in the resource hierarchy.

  Test a value against the result of merging consumer policies in the resource
  hierarchy.

  ## EXAMPLES

  Test for service my-service for current project:

    $ {command} my-service

  Test for service my-service for project `my-project`:

    $ {command} my-service --project=my-project
  """

  @staticmethod
  def Args(parser):
    common_flags.add_resource_args(parser)
    parser.add_argument('service', help='Name of the service.')

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The enablement of the given service or catalog.
    """
    if args.IsSpecified('folder'):
      resource_name = _FOLDER_RESOURCE % args.folder
    elif args.IsSpecified('organization'):
      resource_name = _ORGANIZATION_RESOURCE % args.organization
    elif args.IsSpecified('project'):
      resource_name = _PROJECT_RESOURCE % args.project
    else:
      project = properties.VALUES.core.project.Get(required=True)
      resource_name = _PROJECT_RESOURCE % project

    service_arg, is_catalog = _ParseServiceArg(args.service)

    response = serviceusage.TestEnabled(resource_name, service_arg)
    if args.IsSpecified('format'):
      return response
    log.status.Print(
        _FormatTestEnabledResponse(
            response, args.service, resource_name, is_catalog
        )
    )


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class TestEnabled(base.Command):
  """Test a value against the result of merging consumer policies in the resource hierarchy.

  Test a value against the result of merging consumer policies in the resource
  hierarchy.

  ## EXAMPLES

  Test for service my-service for current project:

    $ {command} my-service

  Test for service my-service for project `my-project`:

    $ {command} my-service --project=my-project

  Test for catalog `catalogs/default-cloud-services` for project `my-project`:

    $ {command} catalogs/default-cloud-services --project=my-project
  """

  @staticmethod
  def Args(parser):
    common_flags.add_resource_args(parser)
    parser.add_argument('service', help='Name of the service or catalog.')

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The enablement of the given service or catalog.
    """
    if args.IsSpecified('folder'):
      resource_name = _FOLDER_RESOURCE % args.folder
    elif args.IsSpecified('organization'):
      resource_name = _ORGANIZATION_RESOURCE % args.organization
    elif args.IsSpecified('project'):
      resource_name = _PROJECT_RESOURCE % args.project
    else:
      project = properties.VALUES.core.project.Get(required=True)
      resource_name = _PROJECT_RESOURCE % project

    service_arg, is_catalog = _ParseServiceArg(args.service)

    response = serviceusage.TestEnabledV2(resource_name, service_arg)
    if args.IsSpecified('format'):
      return response
    log.status.Print(
        _FormatTestEnabledResponse(
            response, args.service, resource_name, is_catalog
        )
    )


