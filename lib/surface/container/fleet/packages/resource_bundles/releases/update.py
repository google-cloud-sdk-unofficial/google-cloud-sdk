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
        To update Release `v1.0.0` for Resource Bundle `my-bundle` in `us-central1`, run:

          $ {command} --version=v1.0.0 --resource-bundle=my-bundle --source=manifest.yaml

        To update a Release with multiple variants in one directory, run:

          $ {command} --version=v1.0.0 --resource-bundle=my-bundle --source=/manifests/ --variants-pattern=manifest-*.yaml

        To update a Release with multiple variants across multiple directories, ex:

          $ {command} --version=v1.0.0 --resource-bundle=my-bundle --source=/manifests/ --variants-pattern=dir-*/
        """,
}


@base.DefaultUniverseOnly
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
    flags.AddVariantsPatternFlag(parser)
    parser.add_argument(
        '--source',
        required=False,
        help="""Source file or directory to update the Release from.
          e.g. ``--source=manifest.yaml'', ``--source=/manifests-dir/''
          Can optionally be paired with the ``--variants-pattern'' arg to create
          multiple variants of a Release.""",
    )

  def Run(self, args):
    """Run the update command."""
    client = apis.ReleasesClient()
    update_mask_attrs = []
    if args.source:
      glob_pattern = utils.GlobPatternFromSourceAndVariantsPattern(
          args.source, args.variants_pattern
      )
      variants = utils.VariantsFromGlobPattern(glob_pattern)
      update_mask_attrs.append('variants')
    else:
      variants = None

    if args.lifecycle:
      update_mask_attrs.append('lifecycle')
    update_mask = ','.join(update_mask_attrs)

    return client.Update(
        release=args.release,
        project=flags.GetProject(args),
        location=flags.GetLocation(args),
        resource_bundle=args.resource_bundle,
        lifecycle=args.lifecycle,
        variants=variants,
        update_mask=update_mask,
    )
