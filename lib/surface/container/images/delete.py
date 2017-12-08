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
"""Delete images command."""

from containerregistry.client import docker_name
from containerregistry.client.v2_2 import docker_session
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import http
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_printer


class Delete(base.DeleteCommand):
  """Delete existing images.

  The container images delete command of gcloud deletes a specified
  tag or digest in a specified repository. Repositories
  must be hosted by the Google Container Registry.
  """

  detailed_help = {
      'DESCRIPTION': """\
          The container images delete command deletes the specified tag or
          digest from the registry. If a tag is specified, only the tag is
          deleted from the registry and image layers remain accessible by
          digest. If a digest is specified, image layers are fully deleted from
          the registry.
      """,
      'EXAMPLES': """\
          Deletes the tag or digest from the input IMAGE_NAME:

            $ {{command}} <IMAGE_NAME>

      """,
  }

  def Collection(self):
    return 'container.images'

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument('image_names', nargs='+',
                        help=('The IMAGE_NAME or IMAGE_NAMES to delete\n'
                              'Format For Digest: *.gcr.io/repository@<digest>'
                              'Format For Tag: *.gcr.io/repository:<tag>'))

  def Run(self, args):
    """This is what ts called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      InvalidImageNameError: If the user specified an invalid image name.
    Returns:
      A list of the deleted docker_name.Tag and docker_name.Digest objects
    """
    # IMAGE_NAME: The fully-qualified image name to delete (with a digest).
    # Deletes the layers. Ex. gcr.io/google-appengine/java(@DIGEST|:TAG).

    http_obj = http.Http()
    # collect input/validate
    digests, tags = self._ProcessImageNames(args.image_names)
    # print
    if digests:
      log.status.Print('Digests:')
    for digest in digests:
      self._PrintDigest(digest, http_obj)

    if tags:
      log.status.Print('Tags:')
    for tag in tags:
      log.status.Print('- '+str(tag))
    for digest in digests:
      tags.update(util.GetDockerTagsForDigest(digest, http_obj))
    # prompt
    console_io.PromptContinue('This operation will delete the above tags '
                              'and/or digests. Tag deletions only delete the'
                              'tag. Digest deletions also delete the '
                              'underlying image layers.',
                              default=True,
                              cancel_on_no=True)
    # delete and collect output
    result = []
    for tag in tags:  # tags must be deleted before digests
      self._DeleteDockerTagOrDigest(tag, http_obj)
      result.append({'name': str(tag)})
    for digest in digests:
      self._DeleteDockerTagOrDigest(digest, http_obj)
      result.append({'name': str(digest)})
    return result

  def _ProcessImageNames(self, image_names):
    digests = set()
    tags = set()
    for image_name in image_names:
      docker_obj = util.GetDockerImageFromTagOrDigest(image_name)
      if isinstance(docker_obj, docker_name.Digest):
        digests.add(docker_obj)
      elif isinstance(docker_obj, docker_name.Tag):
        tags.add(docker_obj)
    return [digests, tags]

  def _DeleteDockerTagOrDigest(self, tag_or_digest, http_obj):
    docker_session.Delete(creds=util.CredentialProvider(),
                          name=tag_or_digest,
                          transport=http_obj)
    log.DeletedResource(tag_or_digest)

  def _DeleteDigestAndAssociatedTags(self, digest, http_obj):
    # digest must not have any tags in order to be deleted
    util.DeleteTagsFromDigest(digest, http_obj)
    tag_list = util.GetTagNamesForDigest(digest, http_obj)
    for tag in tag_list:
      log.DeletedResource(tag)
    docker_session.Delete(creds=util.CredentialProvider(),
                          name=digest,
                          transport=http_obj)
    log.DeletedResource(digest)

  def _PrintDigest(self, digest, http_obj):
    log.status.Print('- '+str(digest))
    self._DisplayDigestTags(digest, http_obj)

  def _DisplayDigestTags(self, digest, http_obj):
    tag_list = util.GetTagNamesForDigest(digest, http_obj)
    if not tag_list:  # no tags on this digest, skip delete prompt
      return
    fmt = ('list[title="  Associated tags:"]')
    resource_printer.Print(tag_list, fmt, out=log.status)
