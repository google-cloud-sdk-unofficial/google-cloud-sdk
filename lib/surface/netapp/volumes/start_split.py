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
"""Starts splitting a Cloud NetApp clone volume from its source volume."""

import textwrap
from googlecloudsdk.api_lib.netapp.volumes import client as volumes_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class StartSplit(base.Command):
  """Starts splitting a Cloud NetApp clone volume from its source volume."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          Starts a split clone operation for a Cloud NetApp clone volume.
          This separates the clone from its source volume and turns it into a standalone volume.
          """),
      'EXAMPLES': textwrap.dedent("""\
          The following command starts a split clone operation for a Volume named `my-clone` in location `us-central1`:

              $ {command} `my-clone` --location=`us-central1`
          """),
  }

  @classmethod
  def Args(cls, parser):
    concept_parsers.ConceptParser([flags.GetVolumePresentationSpec(
        'The Volume to split.')]).AddToParser(parser)
    flags.AddResourceAsyncFlag(parser)

  def Run(self, args):
    """Run the start-split command."""
    volume_ref = args.CONCEPTS.volume.Parse()
    client = volumes_client.VolumesClient(release_track=self._RELEASE_TRACK)
    warning = (
        'You are about to start splitting clone volume'
        f' {volume_ref.RelativeName()}.\nThis will separate it from its source'
        ' volume. This is an irreversible operation.'
    )
    if not console_io.PromptContinue(message=warning):
      return None

    result = client.StartSplit(volume_ref, args.async_)
    if args.async_:
      log.status.Print(
          f'Split clone operation initiated for volume {volume_ref.Name()}.'
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class StartSplitAlpha(StartSplit):
  """Starts splitting a Cloud NetApp clone volume from its source volume."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA
