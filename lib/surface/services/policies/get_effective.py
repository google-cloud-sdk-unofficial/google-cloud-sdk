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
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import properties

_PROJECT_RESOURCE = 'projects/%s'
_FOLDER_RESOURCE = 'folders/%s'
_ORGANIZATION_RESOURCE = 'organizations/%s'


# TODO: b/274633761 - Make command public after suv2 launch.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetEffectivePolicy(base.Command):
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
    common_flags.add_resource_args(parser)

    parser.display_info.AddFormat("""
          table(
            EnabledService:label=EnabledService:sort=1,
            EnabledResources
          )
        """)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Resource name and its parent name.
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

    response = serviceusage.GetEffectivePolicy(
        resource_name + '/effectivePolicy'
    ).enableRuleMetadata

    result = []

    resources = collections.namedtuple(
        'enabledResources', ['EnabledService', 'EnabledResources']
    )

    for metadata in response:
      for values in metadata.enabledResources.additionalProperties:
        result.append(resources(values.key, values.value.resources))
    return result
