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
"""Implements the command to create nand upload attachments to a repository."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import hashlib

from apitools.base.py import transfer
from googlecloudsdk.api_lib.artifacts import exceptions as ar_exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import requests
from googlecloudsdk.command_lib.artifacts import util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import scaled_integer


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  """Creates an Artifact registry attachment in a repository."""

  api_version = 'v1'

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
    To create an attachment for target `projects/myproject/locations/us-central1/packages/mypackage/versions/sha256:123` using a file located in `/path/to/file/sbom.json`:

        $ {command} --target=projects/myproject/locations/us-central1/packages/mypackage/versions/sha256:123
          --files=/path/to/file/sbom.json
    """,
  }

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentPaser.
    """
    flags.GetRequiredAttachmentFlag().AddToParser(parser)
    parser.add_argument(
        '--target',
        metavar='TARGET',
        required=True,
        help='Target of the attachment, should be fully qualified version name',
    )

    parser.add_argument(
        '--attachment-type',
        metavar='ATTACHMENT_TYPE',
        required=True,
        help='Type of the attachment',
    )

    parser.add_argument(
        '--attachment-namespace',
        metavar='ATTACHMENT_NAMESPACE',
        required=False,
        help='Namespace of the attachment',
    )

    parser.add_argument(
        '--files',
        metavar='FILES',
        required=True,
        type=arg_parsers.ArgList(),
        help='Comma-seperated list of files that are part of this attachment',
    )

  def Run(self, args):
    """Run the attachment create command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Result of CreateAttachment operation.

    Raises:
      InvalidInputValueError: when target and attachment
      project/location/repository match.
    """

    client = requests.GetClient()
    messages = client.MESSAGES_MODULE
    attachment_ref = args.CONCEPTS.attachment.Parse()
    target_ref = resources.REGISTRY.ParseRelativeName(
        args.target,
        'artifactregistry.projects.locations.repositories.packages.versions',
    )
    if target_ref.projectsId != attachment_ref.projectsId:
      raise ar_exceptions.InvalidInputValueError(
          'Attachment {} must be in the same project as target {}.'.format(
              attachment_ref.RelativeName(), target_ref.RelativeName()
          )
      )
    if target_ref.locationsId != attachment_ref.locationsId:
      raise ar_exceptions.InvalidInputValueError(
          'Attachment {} must be in the same location as target {}.'.format(
              attachment_ref.RelativeName(), target_ref.RelativeName()
          )
      )
    if target_ref.repositoriesId != attachment_ref.repositoriesId:
      raise ar_exceptions.InvalidInputValueError(
          'Attachment {} must be in the same repository as target {}.'.format(
              attachment_ref.RelativeName(), target_ref.RelativeName()
          )
      )

    file_names = []
    for file in args.files:
      file_name = self.upload_file(
          file, client, messages, attachment_ref.Parent()
      )
      file_names.append(file_name)

    create_request = messages.ArtifactregistryProjectsLocationsRepositoriesAttachmentsCreateRequest(
        attachment=messages.Attachment(
            target=target_ref.RelativeName(),
            type=args.attachment_type,
            attachmentNamespace=args.attachment_namespace,
            files=file_names,
        ),
        parent=attachment_ref.Parent().RelativeName(),
        attachmentId=attachment_ref.attachmentsId,
    )
    op_obj = client.projects_locations_repositories_attachments.Create(
        create_request
    )
    op_ref = resources.REGISTRY.ParseRelativeName(
        op_obj.name, collection='artifactregistry.projects.locations.operations'
    )

    # Handle the operation.
    result = waiter.WaitFor(
        waiter.CloudOperationPollerNoResources(
            client.projects_locations_operations
        ),
        op_ref,
        'Creating Attachment',
    )
    return result

  def upload_file(self, file_path, client, messages, repo_ref):
    # Default chunk size to be consistent for uploading to clouds.
    chunksize = scaled_integer.ParseInteger(
        properties.VALUES.storage.upload_chunk_size.Get()
    )
    request = messages.ArtifactregistryProjectsLocationsRepositoriesFilesUploadRequest(
        uploadFileRequest=messages.UploadFileRequest(),
        parent=repo_ref.RelativeName(),
    )

    mime_type = util.GetMimetype(file_path)
    result_file_name = None
    try:
      upload = transfer.Upload.FromFile(
          file_path, mime_type=mime_type, chunksize=chunksize
      )
      op_obj = client.projects_locations_repositories_files.Upload(
          request, upload=upload
      )
      op = op_obj.operation
      op_ref = resources.REGISTRY.ParseRelativeName(
          op.name, collection='artifactregistry.projects.locations.operations'
      )

      # Handle the operation.
      result = waiter.WaitFor(
          waiter.CloudOperationPoller(
              client.projects_locations_repositories_files,
              client.projects_locations_operations,
          ),
          op_ref,
          'Uploading file: {}'.format(file_path),
      )
      result_file_ref = resources.REGISTRY.ParseRelativeName(
          result.name,
          collection='artifactregistry.projects.locations.repositories.files',
      )
      result_file_name = result_file_ref.RelativeName()
    except waiter.OperationError as e:
      if 'already exists' in str(e):
        log.info(f'File {file_path} already exists'.format(file_path))
        digest = self.computeSha256OfFile(file_path)
        repo_relative_name = repo_ref.RelativeName()
        result_file_name = f'{repo_relative_name}/files/{digest}'
    return result_file_name

  def computeSha256OfFile(self, file_path):
    sha256 = hashlib.sha256()
    data = files.ReadBinaryFileContents(file_path)
    sha256.update(data)
    return 'sha256:' + sha256.hexdigest()
