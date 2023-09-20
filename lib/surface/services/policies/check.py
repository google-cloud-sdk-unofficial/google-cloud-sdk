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
"""services policies check command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_PROJECT_RESOURCE = 'projects/%s'
_FOLDER_RESOURCE = 'folders/%s'
_ORGANIZATION_RESOURCE = 'organizations/%s'
_SERVICE = 'services/%s'


# TODO(b/274633761) make command public after suv2 launch.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Check(base.Command):
  """Check if a service is enabled or can be enabled in the resource or from the resource ancestors.

  Check if a service is enabled or can be enabled in the resource or from the
  resource ancestors.

  ## EXAMPLES

  Check for service my-service for current project:

    $ {command} my-service

  Check for service my-service for project `my-project`:

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
      The enablement of the given service.
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

    response = serviceusage.CheckValue(
        resource_name, _SERVICE % args.service
    ).result

    log.status.Print(
        'service %s is %s for resource %s'
        % (
            args.service,
            response,
            resource_name,
        )
    )
