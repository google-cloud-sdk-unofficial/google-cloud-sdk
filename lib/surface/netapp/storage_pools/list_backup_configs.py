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
"""Lists backup configurations for all volumes in an ONTAP-mode Storage Pool."""

import argparse
import textwrap
from googlecloudsdk.api_lib.netapp.storage_pools import client as storagepools_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBackupConfigs(base.ListCommand):
  """A command to list backup configurations for all volumes in an ONTAP-mode Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          Lists backup configurations for all volumes in an ONTAP-mode Storage Pool.
          """),
      'EXAMPLES': textwrap.dedent("""\
          The following command lists backup configurations in Storage Pool named NAME in location us-central1:

              $ {command} NAME --location=us-central1
          """),
  }

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    concept_parsers.ConceptParser([
        flags.GetStoragePoolPresentationSpec(
            'The Storage Pool to list backup configs for.')
    ]).AddToParser(parser)

  def Run(self, args):
    """Run the list-backup-configs command."""
    properties.VALUES.core.project.GetOrFail()
    storagepool_ref = args.CONCEPTS.storage_pool.Parse()
    client = storagepools_client.StoragePoolsClient(
        release_track=self._RELEASE_TRACK)
    return client.ListBackupConfigs(storagepool_ref, limit=args.limit)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListBackupConfigsAlpha(ListBackupConfigs):
  """A command to list backup configurations for all volumes in an ONTAP-mode Storage Pool."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA
