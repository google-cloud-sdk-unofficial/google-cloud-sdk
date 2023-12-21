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
"""services policies get command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

_PROJECT_RESOURCE = 'projects/{}'
_FOLDER_RESOURCE = 'folders/{}'
_ORGANIZATION_RESOURCE = 'organizations/{}'
_CONSUMER_POLICY_DEFAULT = '/consumerPolicies/{}'


# TODO(b/274633761) make command public after suv2 launch.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Get(base.Command):
  """Get a consumer policy of a project, folder or organization.

  Get a consumer policy of a project, folder or
  organization.

  ## EXAMPLES

   Get consumer policy for default policy on current project:

   $ {command}
      OR
   $ {command} --policy-name=default

   Get consumer policy for default policy on current project and save the
   content in an output file:

   $ {command} --output-file=/path/to/the/file.yaml
       OR
   $ {command} --output-file=/path/to/the/file.json
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--policy-name',
        help=(
            'Name of the consumer policy. Currently only "default" is'
            ' supported.'
        ),
        default='default',
    )
    common_flags.add_resource_args(parser)

    parser.add_argument(
        '--output-file',
        help=(
            'Path to the file to write policy contents to. Supported format:'
            '.yaml or .json.'
        ),
    )

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Resource name and its parent name.
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

    policy = serviceusage.GetConsumerPolicyV2Alpha(
        resource_name + _CONSUMER_POLICY_DEFAULT.format(args.policy_name),
    )

    if args.IsSpecified('output_file'):
      if not (
          args.output_file.endswith('.json')
          or args.output_file.endswith('.yaml')
      ):
        log.error(
            'Invalid output-file format. Please provide path to a yaml or json'
            ' file.'
        )
      else:
        if args.output_file.endswith('.json'):
          data = json.dumps(_ConvertToDict(policy), sort_keys=False)
        else:
          data = yaml.dump(_ConvertToDict(policy), round_trip=True)
        files.WriteFileContents(args.output_file, data)

        log.status.Print(
            'Policy written to the output file %s ' % args.output_file
        )
    else:
      # TODO(b/274633761) Rearrange the ouput in the format:
      # (policy name -> enable rules -> update time -> etag)
      return policy


def _ConvertToDict(policy):
  """ConvertToDict command.

  Args:
    policy: consumerPolicy to be convert to orderedDict.

  Returns:
    orderedDict.
  """

  output = {
      'name': policy.name,
      'enable_rules': [],
      'update_time': policy.updateTime,
      'etag': policy.etag,
      'createTime': policy.createTime,
  }

  for enable_rule in policy.enableRules:
    output['enable_rules'].append({
        'services': list(enable_rule.services),
        'categories': list(enable_rule.categories),
        'groups': list(enable_rule.groups),
    })

  return output
