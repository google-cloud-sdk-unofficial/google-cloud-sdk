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
"""Command to create Release."""

from googlecloudsdk.api_lib.container.fleet.packages import releases as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.packages import flags
from googlecloudsdk.command_lib.container.fleet.packages import utils

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To create Release ``v1.0.0'' for Resource Bundle ``my-bundle'' in ``us-central1'', run:

          $ {command} --version=v1.0.0 --resource-bundle=my-bundle --variants=variant-*.yaml
        """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create Package Rollouts Release."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddResourceBundleFlag(parser)
    flags.AddLocationFlag(parser)
    parser.add_argument(
        '--version', required=True, help='Version of the Release to create.'
    )
    flags.AddLifecycleFlag(parser)
    parser.add_argument(
        '--variants',
        required=True,
        help="""Glob pattern to Variants of the Release.
          ex: --variants=manifest.yaml, --variants=/variants/us-```*```.yaml,
              --variants=/manifests-dir/""",
    )

  def Run(self, args):
    """Run the create command."""
    client = apis.ReleasesClient()
    variants = utils.VariantsFromGlobPattern(args.variants)

    return client.Create(
        resource_bundle=args.resource_bundle,
        version=args.version,
        project=flags.GetProject(args),
        location=flags.GetLocation(args),
        lifecycle=args.lifecycle,
        variants=variants,
    )
