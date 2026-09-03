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
"""Command to look up the configured VPC Service Controls service perimeter for a resource."""

from googlecloudsdk.api_lib.accesscontextmanager import lookup_configured_perimeter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer

DETAILED_HELP = {
    'brief': (
        'Look up the configured VPC Service Controls service perimeter for a'
        ' resource.'
    ),
    'DESCRIPTION': (
        """        Looks up the configured VPC Service Controls service perimeter
        (both enforced and dry-run) that applies to the specified project or folder
        based on resource hierarchy ancestry.
        """
    ),
    'EXAMPLES': (
        """        To look up the configured perimeter for a project with number 1234567890:

          $ {command} --resource=projects/1234567890

        To look up the configured perimeter for a folder with number 9876543210:

          $ {command} --resource=folders/9876543210
        """
    ),
}


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class LookupConfiguredPerimeter(base.DescribeCommand):
  """Look up the configured VPC Service Controls service perimeter for a resource."""

  _API_VERSION = 'v1'
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--resource',
        required=True,
        help=(
            'The resource to look up effective service perimeters for. '
            'Format: `projects/{project_number}` or `folders/{folder_number}`.'
        ),
    )
    parser.display_info.AddFormat('none')

  def Run(self, args):
    client = lookup_configured_perimeter.Client(version=self._API_VERSION)
    return client.LookupConfiguredServicePerimeter(args.resource)

  def Display(self, args, result):
    """Custom display for formatted vertical key-value output."""
    if args.IsSpecified('format'):
      resource_printer.Print(result, args.format)
      return

    log.out.Print(
        'SERVICE_PERIMETER:           {}'.format(result.servicePerimeter or '')
    )
    log.out.Print(
        'RESTRICTED_RESOURCE:         {}'.format(
            result.restrictedResource or ''
        )
    )
    log.out.Print(
        'SERVICE_PERIMETER_DRY_RUN:   {}'.format(
            result.servicePerimeterDryRun or ''
        )
    )
    log.out.Print(
        'RESTRICTED_RESOURCE_DRY_RUN: {}'.format(
            result.restrictedResourceDryRun or ''
        )
    )


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class LookupConfiguredPerimeterBeta(LookupConfiguredPerimeter):
  """Look up the configured VPC Service Controls service perimeter for a resource."""

  _API_VERSION = 'v1'


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class LookupConfiguredPerimeterAlpha(LookupConfiguredPerimeter):
  """Look up the configured VPC Service Controls service perimeter for a resource."""

  _API_VERSION = 'v1alpha'
