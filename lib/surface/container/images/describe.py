# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command to show Container Analysis Data for a specified image."""

from contextlib import contextmanager

from containerregistry.client.v2_2 import docker_http
from googlecloudsdk.api_lib.container.images import container_data_util
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container import flags

# Add to this as we add more container analysis data.
_DEFAULT_KINDS = ['BUILD_DETAILS', 'PACKAGE_VULNERABILITY', 'IMAGE_BASIS']


@contextmanager
def RecoverFromDiagnosticException(image_name):
  try:
    yield
  except docker_http.V2DiagnosticException as err:
    raise util.GcloudifyRecoverableV2Errors(err, {
        403: 'Describe failed, access denied: {0}'.format(image_name),
        404: 'Describe failed, not found: {0}'.format(image_name)
    })


def _CommonArgs(parser, release_track):
  flags.AddTagOrDigestPositional(parser, verb='describe', repeated=False)
  parser.display_info.AddFormat('object')

  if release_track is base.ReleaseTrack.ALPHA:
    parser.add_argument(
        '--occurrence-filter',
        default=' OR '.join(
            ['kind = "{kind}"'.format(kind=x) for x in _DEFAULT_KINDS]),
        help=('Additional filter to fetch occurrences for '
              'a given fully qualified image reference.'))


# pylint: disable=line-too-long
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Lists information about the specified image.

  ## EXAMPLES

  Describe the specified image:

    $ {command} gcr.io/myproject/myimage@digest
          OR
    $ {command} gcr.io/myproject/myimage:tag

  Find the digest for a tag:

    $ {command} gcr.io/myproject/myimage:tag --format='value(digest)'
          OR
    $ {command} gcr.io/myproject/myimage:tag --format='value(fully_qualified_digest)'

  """

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, release_track=base.ReleaseTrack.GA)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      InvalidImageNameError: If the user specified an invalid image name.
    Returns:
      Some value that we want to have printed later.
    """

    with RecoverFromDiagnosticException(args.image_name):
      img_name = util.GetDigestFromName(args.image_name)
      return container_data_util.ContainerData(
          registry=img_name.registry,
          repository=img_name.repository,
          digest=img_name.digest)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(Describe):
  """Lists container analysis data for a given image.

  Lists container analysis data for a valid image.

  ## EXAMPLES

  Describe container analysis data for a specified image:

    $ {command} gcr.io/myproject/myimage@digest
          OR
    $ {command} gcr.io/myproject/myimage:tag
  """

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, release_track=base.ReleaseTrack.ALPHA)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      InvalidImageNameError: If the user specified an invalid image name.
    Returns:
      Some value that we want to have printed later.
    """

    with RecoverFromDiagnosticException(args.image_name):
      img_name = util.GetDigestFromName(args.image_name)
      return util.TransformContainerAnalysisData(img_name,
                                                 args.occurrence_filter)
