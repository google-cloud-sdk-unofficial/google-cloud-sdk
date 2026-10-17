# -*- coding: utf-8 -*- #
# Copyright 2026 Google Inc. All Rights Reserved.
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
"""services list-dependents command."""
import collections
import sys

from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import properties

_PROJECT_RESOURCE = 'projects/{}'
_FOLDER_RESOURCE = 'folders/{}'
_ORGANIZATION_RESOURCE = 'organizations/{}'
_SERVICE_PREFIX = 'services/'
_Service = collections.namedtuple('Service', ['name'])


def _GetServiceName(service: str) -> str:
  if not service.startswith(_SERVICE_PREFIX):
    return f'{_SERVICE_PREFIX}{service}'
  return service


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.RegionalEndpointsSupported
class ListDependents(base.ListCommand):
  """List services that depend on a specific service.

  List services that depend on a specific service.

  ## EXAMPLES

   List services that depend on service my-service:

    $ {command} my-service

   List services that depend on service my-service for a specific project
   '12345678':

    $ {command} my-service --project=12345678
  """

  @staticmethod
  def Args(parser):
    parser.add_argument('service', help='Name of the service.')
    common_flags.add_resource_args(parser)

    base.PAGE_SIZE_FLAG.SetDefault(parser, 50)

    # Remove unneeded list-related flags from parser
    base.URI_FLAG.RemoveFromParser(parser)

    parser.display_info.AddFormat("""
          table(
            name:label=NAME:sort=1
          )
        """)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      List of services that depend on the given service.
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

    service = _GetServiceName(args.service)

    if args.IsSpecified('limit'):
      limit = args.limit
    else:
      limit = sys.maxsize

    response = serviceusage.ListDependentServicesV2(
        resource_name,
        service,
        args.page_size,
        limit=limit,
    )

    return [_Service(name=dep) for dep in response]
