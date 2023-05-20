# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Implements the command to list SBOM file references."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import sbom_util

DEFAULT_LIST_FORMAT = """\
    flattened(
      occ.resource.uri:label=resource_uri,
      occ.sbomReference.payload.predicate.location,
      occ.name:label=reference,
      file_info.exists:label=file_exists,
      file_info.err_msg:label=file_err_msg
    )"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
class List(base.ListCommand):
  """List SBOM file references."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To list SBOM file references:

          $ {command}

          To list SBOM file references related to the repository "us-east1-docker.pkg.dev/project/repo":

          $ {command} --resource="us-east1-docker.pkg.dev/project/repo"

          To list SBOM file references related to the image with the tag "us-east1-docker.pkg.dev/project/repo/my-image:1.0":

          $ {command} --resource="us-east1-docker.pkg.dev/project/repo/my-image:1.0"

          To list SBOM file references related to the image with the digest "us-east1-docker.pkg.dev/project/repo/my-image@sha256:88b205d7995332e10e836514fbfd59ecaf8976fc15060cd66e85cdcebe7fb356":

          $ {command} --resource="us-east1-docker.pkg.dev/project/repo/my-image@sha256:88b205d7995332e10e836514fbfd59ecaf8976fc15060cd66e85cdcebe7fb356"

          To list SBOM file references generated when the images were pushed to Artifact Registry and related to the installed package dependency "perl":

          $ {command} --installed-package="perl"

          """,
  }

  @staticmethod
  def Args(parser):
    """Set up arguements for this command.

    Args:
      parser: An argparse.ArgumentPaser.
    """
    parser.display_info.AddFormat(DEFAULT_LIST_FORMAT)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--installed-package',
        required=False,
        help=(
            'List SBOM file references generated when the images were pushed to'
            ' Artifact Registry and related to the installed package'
            ' dependency. See'
            ' https://cloud.google.com/container-analysis/docs/scanning-types'
            ' for supported packages.'
        ),
    )
    parser.add_argument(
        '--resource',
        required=False,
        help=(
            'List SBOM file references related to the resource uri. It can be'
            ' a repository or an image.'
        ),
    )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A list of SBOM references.
    """
    return sbom_util.ListSbomReferences(args)
