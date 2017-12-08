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

import argparse

from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import http

# Add to this as we add columns.
_DEFAULT_KINDS = [
    'BUILD_DETAILS',
    'IMAGE_BASIS',
    'PACKAGE_VULNERABILITY',
]


class ListTags(base.ListCommand):
  """List tags and digests for the specified image."""

  detailed_help = {
      'DESCRIPTION':
          """\
          The container images list-tags command of gcloud lists metadata about
          tags and digests for the specified container image. Images must be
          hosted by the Google Container Registry.
      """,
      'EXAMPLES':
          """\
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
        '--show-occurrences',
        action='store_true',
        default=False,
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--occurrence-filter',
        default=' OR '.join(
            ['kind = "{kind}"'.format(kind=x) for x in _DEFAULT_KINDS]),
        help=argparse.SUPPRESS)
    parser.add_argument(
        'image',
        help='The name of the image. Format: *.gcr.io/repository/image')

    # Does nothing for us, included in base.ListCommand
    base.URI_FLAG.RemoveFromParser(parser)

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

    repository = util.ValidateRepositoryPath(args.image)
    http_obj = http.Http()
    with docker_image.FromRegistry(
        basic_creds=util.CredentialProvider(),
        name=repository,
        transport=http_obj) as image:
      try:
        return util.TransformManifests(
            image.manifests(),
            repository,
            show_occurrences=args.show_occurrences,
            occurrence_filter=args.occurrence_filter)
      except docker_http.V2DiagnosticException as err:
        raise util.GcloudifyRecoverableV2Errors(err, {
            403: 'Access denied: {0}'.format(repository),
            404: 'Not found: {0}'.format(repository)
        })
