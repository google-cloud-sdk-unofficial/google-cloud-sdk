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

# TODO: b/300099033 - Capitalize and turn into a sentence.
"""services policies get-effective-policy command."""

import collections

from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_PROJECT_RESOURCE = 'projects/{}'
_FOLDER_RESOURCE = 'folders/{}'
_ORGANIZATION_RESOURCE = 'organizations/{}'


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class GetEffectivePolicyBeta(base.Command):
  """Get effective policy for a project, folder or organization.

  Get effective policy for a project, folder or organization.

  ## EXAMPLES

   Get effective policy for the current project:

   $ {command}

   Get effective policy for project `my-project`:

   $ {command} --project=my-project
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--view',
        help=(
            'The view of the effective policy. BASIC includes basic metadata'
            ' about the effective policy. FULL includes every information'
            ' related to effective policy.'
        ),
        default='BASIC',
        choices=['BASIC', 'FULL'],
    )
    common_flags.add_resource_args(parser)

    parser.display_info.AddFormat("""
          table(
            Enabled:label=Enabled:sort=1,
            EnabledPolicies:label=EnabledPolicies
          )
        """)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Effective Policy.
    """
    if args.IsSpecified('folder'):
      resource_name = _FOLDER_RESOURCE.format(args.folder)
    elif args.IsSpecified('organization'):
      resource_name = _ORGANIZATION_RESOURCE.format(args.organization)
    elif args.IsSpecified('project'):
      resource_name = _PROJECT_RESOURCE.format(args.project)
    else:
      project = properties.VALUES.core.project.Get(required=True)
      resource_name = _PROJECT_RESOURCE.format(project)

    response = serviceusage.GetEffectivePolicyV2Beta(
        resource_name + '/effectivePolicy', args.view
    )

    if args.IsSpecified('format'):
      return response
    else:
      log.status.Print('EnabledRules:')
      for enable_rule in response.enableRules:
        if enable_rule.services:
          log.status.Print(' Services:')
          for service in enable_rule.services:
            log.status.Print('  - %s' % service)
        if enable_rule.catalogs:
          log.status.Print(' Catalogs:')
          for catalog in enable_rule.catalogs:
            log.status.Print('  - %s' % catalog)

      if args.view == 'FULL':
        log.status.Print('\nMetadata of effective policy:')
        result = []

        resources = collections.namedtuple(
            'ruleSources', ['Enabled', 'EnabledPolicies']
        )

        for metadata in response.enableRuleMetadata or []:
          if (
              metadata.serviceSources
              and metadata.serviceSources.additionalProperties
          ):
            for values in metadata.serviceSources.additionalProperties:
              result.append(resources(values.key, values.value.policies))
          if (
              metadata.catalogSources
              and metadata.catalogSources.additionalProperties
          ):
            for values in metadata.catalogSources.additionalProperties:
              result.append(resources(values.key, values.value.policies))
        return result


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class GetEffectivePolicy(base.Command):
  """Get the effective policy for a project, folder or organization.

  Get the effective policy for a project, folder or organization.

  ## EXAMPLES

   Get effective policy for the current project:

   $ {command}

   Get effective policy for project `my-project`:

   $ {command} --project=my-project
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--view',
        help=(
            'The view of the effective policy. BASIC includes basic metadata'
            ' about the effective policy. FULL includes every information'
            ' related to effective policy.'
        ),
        default='BASIC',
        choices=['BASIC', 'FULL'],
    )
    common_flags.add_resource_args(parser)

    parser.display_info.AddFormat("""
          table(
            Enabled:label=Enabled:sort=1,
            EnabledPolicies:label=EnabledPolicies
          )
        """)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Effective Policy.
    """
    if args.IsSpecified('folder'):
      resource_name = _FOLDER_RESOURCE.format(args.folder)
    elif args.IsSpecified('organization'):
      resource_name = _ORGANIZATION_RESOURCE.format(args.organization)
    elif args.IsSpecified('project'):
      resource_name = _PROJECT_RESOURCE.format(args.project)
    else:
      project = properties.VALUES.core.project.Get(required=True)
      resource_name = _PROJECT_RESOURCE.format(project)

    response = serviceusage.GetEffectivePolicyV2(
        resource_name + '/effectivePolicy', args.view
    )

    if args.IsSpecified('format'):
      return response
    else:
      log.status.Print('EnabledRules:')
      for enable_rule in response.enableRules:
        if enable_rule.services:
          log.status.Print(' Services:')
          for service in enable_rule.services:
            log.status.Print('  - %s' % service)
        if enable_rule.catalogs:
          log.status.Print(' Catalogs:')
          for catalog in enable_rule.catalogs:
            log.status.Print('  - %s' % catalog)

      if args.view == 'FULL':
        log.status.Print('\nMetadata of effective policy:')
        result = []

        resources = collections.namedtuple(
            'ruleSources', ['Enabled', 'EnabledPolicies']
        )

        for metadata in response.enableRuleMetadata or []:
          if (
              metadata.serviceSources
              and metadata.serviceSources.additionalProperties
          ):
            for values in metadata.serviceSources.additionalProperties:
              result.append(resources(values.key, values.value.policies))
          if (
              metadata.catalogSources
              and metadata.catalogSources.additionalProperties
          ):
            for values in metadata.catalogSources.additionalProperties:
              result.append(resources(values.key, values.value.policies))
        return result
