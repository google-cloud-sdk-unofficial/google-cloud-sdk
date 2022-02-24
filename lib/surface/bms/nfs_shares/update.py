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
"""Bare Metal Solution NFS share update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import exceptions
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a Bare Metal Solution NFS share.

          This call returns immediately, but the update operation may take
          several minutes to complete. To check if the operation is complete,
          use the `describe` command for the NFS share.
        """,
    'EXAMPLES':
        """
          To update an NFS share called ``my-share'' in region ``us-central1'' with
          a new label ``key1=value1'', run:

          $ {command} my-share  --region=us-central1 --update-labels=key1=value1

          To clear all labels, run:

          $ {command} my-share --region=us-central1 --clear-labels

          To remove label ``key1'', run:

          $ {command} my-share --region=us-central1 --remove-labels=key1
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a Bare Metal Solution NFS share."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNfsShareArgToParser(parser, positional=True)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if not labels_diff.MayHaveUpdates():
      raise exceptions.NoConfigurationChangeError(
          'No configuration change was requested. Did you mean to include the '
          'flags `--update-labels` `--delete-labels` or `--clear-labels`?')

    nfs_share = args.CONCEPTS.nfs_share.Parse()
    client = BmsClient()
    orig_resource = client.GetNfsShare(nfs_share)
    labels_update = labels_diff.Apply(client.messages.NfsShare.LabelsValue,
                                      orig_resource.labels).GetOrNone()

    op_ref = client.UpdateNfsShare(
        nfs_share_resource=nfs_share, labels=labels_update)
    log.status.Print('Update request issued for: [{}]\nThis may take several '
                     'minutes to complete.'.format(nfs_share.Name()))
    return op_ref


Update.detailed_help = DETAILED_HELP
