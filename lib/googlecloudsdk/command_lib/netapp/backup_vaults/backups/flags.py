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
"""Flags and helpers for the Cloud NetApp Backups commands."""


import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers


BACKUP_VAULTS_LIST_FORMAT = """\
    table(
        name.basename():label=BACKUP_NAME:sort=1,
        name.segment(3):label=LOCATION,
        backupVault,
        sourceVolume,
        sourceSnapshot,
        state
    )"""


## Helper functions to add backup flags ##


def AddBackupBackupVaultResourceArg(parser, required=True):
  group_help = (
      'The Backup Vault that the Backup is stored in'
  )
  concept_parsers.ConceptParser.ForResource(
      '--backup-vault',
      flags.GetBackupVaultResourceSpec(positional=False),
      group_help=group_help,
      required=required,
      flag_name_overrides={'location': ''},
  ).AddToParser(parser)


def AddBackupSourceVolumeResourceArg(parser, required=True):
  group_help = (
      """The full name of the Source Volume that the Backup is based on',
      Format: `projects/{projects_id}/locations/{location}/volumes/{volume_id}`
      """
  )
  concept_parsers.ConceptParser.ForResource(
      '--source-volume',
      flags.GetVolumeResourceSpec(positional=False),
      group_help=group_help,
      required=required,
      flag_name_overrides={'location': ''},
  ).AddToParser(parser)


def AddBackupSourceSnapshotResourceArg(parser):
  group_help = (
      """
      The full name of the Source Snapshot that the Backup is based on',
      Format: `projects/{project_id}/locations/{location}/volumes/{volume_id}/snapshots/{snapshot_id}`
      """
  )
  concept_parsers.ConceptParser.ForResource(
      '--source-snapshot',
      flags.GetSnapshotResourceSpec(source_snapshot_op=True, positional=False),
      group_help=group_help,
      flag_name_overrides={'location': '', 'volume': ''},
  ).AddToParser(parser)


def AddBackupOntapSourceArg(parser):
  """Add the ONTAP Source arg to the arg parser."""
  ontap_source_arg_spec = {
      'storage-pool': str,
      'volume-uuid': str,
      'snapshot-uuid': str,
  }
  ontap_source_help = textwrap.dedent("""\
    ONTAP source for the backup.

    It consists of the following fields:
    * `storage-pool`: The storage pool of the source volume.
    * `volume-uuid`: The UUID of the source volume.
    * `snapshot-uuid`: The UUID of the source snapshot (optional).
    """)
  parser.add_argument(
      '--ontap-source',
      type=arg_parsers.ArgDict(
          spec=ontap_source_arg_spec,
          required_keys=['storage-pool', 'volume-uuid'],
      ),
      help=ontap_source_help,
      required=False,
  )


## Helper functions to combine Backups args / flags for gcloud commands ##


def AddBackupCreateArgs(parser, support_ontap_source=False):
  """Add args for creating a Backup."""
  concept_parsers.ConceptParser(
      [flags.GetBackupPresentationSpec('The Backup to create')]
  ).AddToParser(parser)
  AddBackupBackupVaultResourceArg(parser, required=True)

  if support_ontap_source:
    source_group = parser.add_mutually_exclusive_group(required=True)
    vol_snap_group = source_group.add_group()
    AddBackupSourceVolumeResourceArg(vol_snap_group, required=True)
    AddBackupSourceSnapshotResourceArg(vol_snap_group)
    AddBackupOntapSourceArg(source_group)
  else:
    AddBackupSourceVolumeResourceArg(parser, required=True)
    AddBackupSourceSnapshotResourceArg(parser)
  flags.AddResourceDescriptionArg(parser, 'Backup Vault')
  flags.AddResourceAsyncFlag(parser)
  labels_util.AddCreateLabelsFlags(parser)


def AddBackupDeleteArgs(parser):
  """Add args for deleting a Backup Vault."""
  concept_parsers.ConceptParser(
      [flags.GetBackupPresentationSpec('The Backup to delete')]
  ).AddToParser(parser)
  flags.AddResourceAsyncFlag(parser)


def AddBackupUpdateArgs(parser):
  """Add args for updating a Backup."""
  concept_parsers.ConceptParser(
      [flags.GetBackupPresentationSpec('The Backup to update')]
  ).AddToParser(parser)
  AddBackupBackupVaultResourceArg(parser, required=True)
  flags.AddResourceDescriptionArg(parser, 'Backup')
  flags.AddResourceAsyncFlag(parser)
  labels_util.AddUpdateLabelsFlags(parser)
