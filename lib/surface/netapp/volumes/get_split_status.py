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
"""Retrieves the split status of a Cloud NetApp clone volume."""

import textwrap
from googlecloudsdk.api_lib.netapp.volumes import client as volumes_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class GetSplitStatus(base.DescribeCommand):
  """Retrieves the split status of a Cloud NetApp clone volume."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          Retrieves the current split clone status for a Cloud NetApp clone volume.
          """),
      'EXAMPLES': textwrap.dedent("""\
          The following command retrieves split status for a Volume named `my-clone` in location `us-central1`:

              $ {command} `my-clone` --location=`us-central1`
          """),
  }

  @classmethod
  def Args(cls, parser):
    concept_parsers.ConceptParser([flags.GetVolumePresentationSpec(
        'The Volume to retrieve split status for.')]).AddToParser(parser)

  def Run(self, args):
    """Run the get-split-status command."""
    volume_ref = args.CONCEPTS.volume.Parse()
    client = volumes_client.VolumesClient(release_track=self._RELEASE_TRACK)
    return client.GetSplitStatus(volume_ref)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetSplitStatusAlpha(GetSplitStatus):
  """Retrieves the split status of a Cloud NetApp clone volume."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA
