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
"""services catalogs list-members command."""
import collections
import sys

from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_PROJECT_RESOURCE = 'projects/{}'
_FOLDER_RESOURCE = 'folders/{}'
_ORGANIZATION_RESOURCE = 'organizations/{}'
_CATALOG_PREFIX = 'catalogs/'
_Member = collections.namedtuple('Member', ['name'])


def _GetCatalogName(name: str) -> str:
  if not name.startswith(_CATALOG_PREFIX):
    return f'{_CATALOG_PREFIX}{name}'
  return name


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.RegionalEndpointsSupported
class ListCatalogMembers(base.ListCommand):
  """List members of a specific catalog.

  List members of a specific catalog. Currently, only `default-cloud-services`
  is supported.

  ## EXAMPLES

   List members of catalog `default-cloud-services`:

    $ {command} --name=default-cloud-services

   List members of catalog `default-cloud-services` for a specific project
   `12345678`:

    $ {command} --name=default-cloud-services --project=12345678
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--name',
        required=True,
        help=(
            'Name of the catalog. Currently, only'
            " 'default-cloud-services' is supported."
        ),
    )
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
      List of services in the catalog.
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

    catalog = _GetCatalogName(args.name)

    if args.IsSpecified('limit'):
      limit = args.limit
    else:
      limit = sys.maxsize

    try:
      response = serviceusage.ListCatalogMembersV2(
          resource_name,
          catalog,
          args.page_size,
          limit=limit,
      )
    except exceptions.CatalogNotFoundError:
      log.warning('Catalog not found.')
      return []

    return [_Member(name=service) for service in response]
