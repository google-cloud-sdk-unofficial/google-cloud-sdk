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
"""Command for listing image-view resources."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.universe_descriptor import universe_descriptor

LIST_FORMAT = """\
    table(
      image.name:label=NAME,
      image.selfLink.map().scope(projects).segment(0):label=PROJECT,
      image.family:label=FAMILY,
      image.deprecated.state:label=DEPRECATED,
      image.status:label=STATUS
    )"""


def _PublicImageProjects():
  if properties.IsDefaultUniverse():
    return sorted(constants.PUBLIC_IMAGE_PROJECTS)
  else:
    prefix = (
        universe_descriptor.UniverseDescriptor()
        .Get(properties.GetUniverseDomain())
        .project_prefix
    )
    return [
        prefix + ':' + project
        for project in sorted(constants.BASE_PUBLIC_IMAGE_PROJECTS)
    ]


def _Args(parser):
  """Helper function for arguments."""
  parser.display_info.AddFormat(LIST_FORMAT)
  lister.AddBaseListerArgs(parser)

  compute_flags.AddRegionFlag(
      parser,
      resource_type='image-view',
      operation_type='list',
      help_text='The region of the image-view resources to list.',
  )

  parser.add_argument(
      '--show-deprecated',
      action='store_true',
      help='If provided, deprecated images are shown.',
  )

  if constants.PREVIEW_IMAGE_PROJECTS:
    preview_image_projects = '{0}.'.format(
        ', '.join(constants.PREVIEW_IMAGE_PROJECTS)
    )
  else:
    preview_image_projects = '(none)'

  parser.add_argument(
      '--preview-images',
      action='store_true',
      default=False,
      help="""\
        Show image views that are in limited preview. The preview image projects
        are: {0}
        """.format(preview_image_projects),
  )
  parser.add_argument(
      '--show-preview-images',
      dest='preview_images',
      action='store_true',
      hidden=True,
      help=(
          'When this flag is enabled, gcloud expands the scope of projects it '
          'queries. '
          'In addition to standard and user project images, it will '
          "also include images hosted in Google Cloud's limited-preview image "
          'projects.'
      ),
  )

  parser.add_argument(
      '--standard-images',
      action='store_true',
      default=True,
      help="""\
       List image views from public image projects. The public image projects
       that are available include the following: {0}.
       """.format(', '.join(constants.PUBLIC_IMAGE_PROJECTS)),
  )


@base.RegionalEndpointsSupported
@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.GA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.ALPHA,
)
class List(base.ListCommand):
  """List Compute Engine image-view resources."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args):
    """Yields image views from (potentially) multiple projects."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseNamesAndRegexpFlags(args, holder.resources)

    region = properties.VALUES.compute.region.GetOrFail()

    def ParseRegion(project):
      return holder.resources.Parse(
          region, {'project': project}, collection='compute.regions'
      )

    scope_set = lister.RegionSet(
        [ParseRegion(properties.VALUES.core.project.GetOrFail())]
    )

    if args.standard_images:
      for project in _PublicImageProjects():
        scope_set.add(ParseRegion(project))

    if args.preview_images:
      for project in constants.PREVIEW_IMAGE_PROJECTS:
        scope_set.add(ParseRegion(project))

    request_data = lister._Frontend(  # pylint: disable=protected-access
        request_data.filter, request_data.max_results, scope_set
    )

    list_implementation = lister.MultiScopeLister(
        client, regional_service=client.apitools_client.imageViews
    )

    image_views = lister.Invoke(request_data, list_implementation)

    return self._FilterDeprecated(args, image_views)

  def _CheckForDeprecated(self, image_view):
    image = image_view.get('image')
    if image is not None:
      deprecate_info = image.get('deprecated')
      if deprecate_info is not None:
        image_state = deprecate_info.get('state')
        if image_state and image_state != 'ACTIVE':
          return True
    return False

  def _FilterDeprecated(self, args, image_views):
    for image_view in image_views:
      if not self._CheckForDeprecated(image_view) or args.show_deprecated:
        yield image_view


List.detailed_help = {
    'brief': 'List Compute Engine image-view resources.',
    'DESCRIPTION': """\
        *{command}* lists Compute Engine image-view resources in a given
        project and region.

        By default, image views from both the current project and public image
        projects (e.g. `debian-cloud`, `ubuntu-os-cloud`) are listed. Use
        `--no-standard-images` to list only image views from the current
        project.
        """,
    'EXAMPLES': """\
        To list all image-view resources in a project in region `us-central1`:

          $ {command} --region=us-central1

        To list all image-view resources with a specific source disk in region `us-central1`:

          $ {command} --region=us-central1 --filter="image.sourceDisk:test-disk-us-central1-ir1"
        """,
}
