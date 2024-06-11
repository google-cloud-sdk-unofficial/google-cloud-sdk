# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command to list all Releases of a Resource Bundle."""

from googlecloudsdk.api_lib.container.fleet.packages import releases as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.packages import flags

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To list all Releases for bundle `cert-manager` in `us-central1`, run:

          $ {command} --resource-bundle=cert-manager --location=us-central1
        """,
}

# For more formatting options see:
# http://cloud/sdk/gcloud/reference/topic/formats
_FORMAT = 'table(name.basename(), lifecycle, createTime)'


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Releases of a Resource Bundle."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(apis.GetReleaseURI)
    flags.AddLocationFlag(parser)
    flags.AddResourceBundleFlag(parser)

  def Run(self, args):
    """Run the list command."""
    client = apis.ReleasesClient()
    return client.List(
        project=flags.GetProject(args),
        location=flags.GetLocation(args),
        parent_bundle=args.resource_bundle,
        limit=args.limit,
        page_size=args.page_size,
    )
