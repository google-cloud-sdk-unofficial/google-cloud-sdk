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
"""Implements the command to upload an SBOM file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import sbom_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
class Load(base.Command):
  """Upload an SBOM file and create a reference occurrence."""
  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To upload an SBOM file at /path/to/sbom.json for a docker image in Artifact Registry:

          $ {command} --source=/path/to/sbom --uri=us-west1-docker.pkg.dev/my-project/my-repository/busy-box@sha256:abcxyz
          """,
  }

  @staticmethod
  def Args(parser):
    """Set up arguements for this command.

    Args:
      parser: An argparse.ArgumentPaser.
    """
    parser.add_argument(
        '--source',
        metavar='SOURCE',
        required=True,
        default='.',
        help='The SBOM file for uploading.')
    parser.add_argument(
        '--uri',
        metavar='ARTIFACT_URI',
        required=True,
        help='The URI of artifact the SBOM is generated from.')

  def Run(self, args):
    """Run the load command."""
    # Parse file and get the version.
    s = sbom_util.ParseJsonSbom(args.source)
    log.info('Successfully loaded the sbom file. Format: {0}-{1}.'.format(
        s.sbom_format, s.version))

    # Get information from the artifact.
    a = sbom_util.ProcessArtifact(args.uri)
    log.info(('Processed artifact. ' +
              'Project: {0}, Location: {1}, URI: {2}, Digest {3}.').format(
                  a.project, a.location, a.resource_uri, a.digest))

    # Find the bucket for uploading.

    # Upload SBOM.

    # Write reference occurrence.
