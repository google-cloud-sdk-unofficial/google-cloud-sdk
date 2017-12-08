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
"""List tags command."""

from containerregistry.client.v2 import docker_image
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import http


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List tags and digests for the specified image."""

  detailed_help = {
      'DESCRIPTION': """\
          The container images list-tags command of gcloud lists metadata about
          tags and digests for the specified container image. Images must be
          hosted by the Google Container Registry.
      """,
      'EXAMPLES': """\
          List the tags in a specified image:

            $ {{command}} gcr.io/myproject/myimage

      """,
  }

  def Collection(self):
    return 'container.tags'

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        'image',
        help='The name of the image. Format: *.gcr.io/repository/image')

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

    repository = util.ValidateImage(args.image)
    http_obj = http.Http()
    with docker_image.FromRegistry(
        basic_creds=util.CredentialProvider(),
        name=repository,
        transport=http_obj) as image:
      return util.TransformManifests(image.manifests())
