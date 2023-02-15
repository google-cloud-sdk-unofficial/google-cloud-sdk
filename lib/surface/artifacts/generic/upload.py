# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Implements the command to upload Generic artifacts to a repository."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import transfer
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import util
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
@base.Hidden
class Upload(base.Command):
  """Upload a generic artifact to an artifact repository."""

  api_version = 'v1'

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
    To upload version v0.1.0 of a generic artifact located in /path/to/file/ to a repository in "us-central1":

        $ {command} --location=us-central1 --project=myproject --repository=myrepo \
          --package=mypackage --version=v0.1.0 --source=/path/to/file/
    """,
  }

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentPaser.
    """
    flags.GetRequiredRepoFlag().AddToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)

    parser.add_argument(
        '--source',
        metavar='SOURCE',
        required=True,
        help='The path to the file you are uploading.')
    parser.add_argument(
        '--package',
        metavar='PACKAGE',
        required=True,
        help='The package to upload.')
    parser.add_argument(
        '--version',
        metavar='VERSION',
        required=True,
        help='The version of the package. You cannot overwrite an existing version in the repository.'
    )

  def Run(self, args):
    """Run the generic artifact upload command."""

    client = apis.GetClientInstance('artifactregistry', self.api_version)
    client.additional_http_headers['X-Goog-Upload-Protocol'] = 'multipart'
    messages = client.MESSAGES_MODULE

    # Upload the generic artifact.
    repo_ref = args.CONCEPTS.repository.Parse()
    file_name = args.source.split('/')[-1]

    request = messages.ArtifactregistryProjectsLocationsRepositoriesGenericArtifactsUploadRequest(
        uploadGenericArtifactRequest=messages.UploadGenericArtifactRequest(
            packageId=args.package,
            versionId=args.version,
            filename=file_name),
        parent=repo_ref.RelativeName())

    mime_type = util.GetMimetype(args.source)
    upload = transfer.Upload.FromFile(args.source, mime_type=mime_type)
    op_obj = client.projects_locations_repositories_genericArtifacts.Upload(
        request, upload=upload)
    op = op_obj.operation
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='artifactregistry.projects.locations.operations')

    # Handle the operation.
    if args.async_:
      return op_ref
    else:
      result = waiter.WaitFor(
          waiter.CloudOperationPollerNoResources(
              client.projects_locations_operations), op_ref,
          'Uploading file')
      return result
