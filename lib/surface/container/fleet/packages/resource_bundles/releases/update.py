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
"""Command to update Release."""

from googlecloudsdk.api_lib.container.fleet.packages import releases as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.packages import flags
from googlecloudsdk.command_lib.container.fleet.packages import utils

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To update Release ``v1.0.0'' of ``cert-manager'' in ``us-central1'', run:

          $ {command} v1.0.0 --location=us-central1 --resource-bundle=cert-manager --lifecycle=published --variants=variant-*.yaml
        """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update Package Rollouts Release."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddReleaseFlag(parser)
    flags.AddLocationFlag(parser)
    flags.AddResourceBundleFlag(parser)
    flags.AddLifecycleFlag(parser)
    parser.add_argument(
        '--variants',
        required=False,
        help='Glob pattern to variants of the Release.',
    )
    parser.add_argument(
        '--update-mask',
        required=False,
        help='Mask denoting which fields to update.',
    )

  def Run(self, args):
    """Run the update command."""
    client = apis.ReleasesClient()
    variants = utils.VariantsFromGlobPattern(args.variants)

    return client.Update(
        release=args.release,
        project=flags.GetProject(args),
        location=flags.GetLocation(args),
        resource_bundle=args.resource_bundle,
        lifecycle=args.lifecycle,
        variants=variants,
        update_mask=args.update_mask,
    )
