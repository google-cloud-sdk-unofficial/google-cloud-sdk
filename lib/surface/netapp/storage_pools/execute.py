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

"""Execute an ONTAP CLI command for Cloud NetApp Volumes."""

from googlecloudsdk.api_lib.netapp.ontap import client as ontap_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp.storage_pools import flags as storagepools_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Execute(base.Command):
  """Execute an ONTAP CLI command."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([
        flags.GetOntapModeStoragePoolPresentationSpec(
            'The Storage Pool to target.'
        )
    ]).AddToParser(parser)
    storagepools_flags.AddOntapCommandArg(parser)

  def _GetOntapClient(self):
    """Returns an instance of OntapClient."""

    return ontap_client.OntapClient(self._RELEASE_TRACK)

  def Run(self, args):
    storage_pool_ref = args.CONCEPTS.storage_pool.Parse()
    client = self._GetOntapClient()
    return client.execute_ontap_post(storage_pool_ref, args.ontap_command)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ExecuteBeta(Execute):
  """Execute an ONTAP CLI command."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ExecuteAlpha(ExecuteBeta):
  """Execute an ONTAP CLI command."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA
