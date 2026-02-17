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

import textwrap

from googlecloudsdk.api_lib.container.fleet.packages import releases as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.packages import flags
from googlecloudsdk.command_lib.container.fleet.packages import utils

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': textwrap.dedent(""" \
        To create Release `v1.0.0` for Resource Bundle `my-bundle`, run:

          $ {command} --version=v1.0.0 --resource-bundle=my-bundle --source=<SOURCE_PATH>

        SOURCE_PATH could be a one of the following:
        - A glob pattern for manifest files, e.g. `/manifests-dir/*.yaml`. This will create a Variant for each matching file, inferring the Variant name from the file name, e.g. `manifest-1.yaml` will be used to create `manifest-1` Variant.
        - A glob pattern for directories of manifest files, e.g. `/manifests-dirs/*`. This will create a Variant for each matching directory, inferring the Variant name from the directory name, e.g. `/manifests-dirs/manifest-1` will be used to create `manifest-1` Variant. All YAML files under `/manifests-dirs/manifest-1/` folder and its subfolders will be used to create the Variant.
        """),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create Package Rollouts Release."""

  detailed_help = _DETAILED_HELP
  _api_version = 'v1'

  @staticmethod
  def Args(parser):
    flags.AddResourceBundleFlag(parser)
    flags.AddLocationFlag(parser)
    parser.add_argument(
        '--version', required=True, help='Version of the Release to create.'
    )
    flags.AddLifecycleFlag(parser)
    parser.add_argument(
        '--source',
        required=True,
        help="""Source file or directory to create the Release from.
          e.g. ``--source=manifest.yaml'', ``--source=/manifests-dir/'',
          ``--source=/manifests-dir/*.yaml''""",
    )
    flags.AddSkipCreatingVariantResourcesFlag(parser)

  def Run(self, args):
    """Run the create command."""
    client = apis.ReleasesClient(self._api_version)
    variants = utils.VariantsFromGlobPattern(args.source)

    return client.Create(
        resource_bundle=args.resource_bundle,
        version=args.version,
        project=flags.GetProject(args),
        location=flags.GetLocation(args),
        lifecycle=args.lifecycle,
        variants=variants,
        skip_creating_variant_resources=args.skip_creating_variant_resources,
    )


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create Package Rollouts Release."""

  _api_version = 'v1beta'


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create Package Rollouts Release."""

  _api_version = 'v1alpha'
