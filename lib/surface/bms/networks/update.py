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
"""Bare Metal Solution network update command."""

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
          Update a Bare Metal Solution network.

          This call returns immediately, but the update operation may take
          several minutes to complete. To check if the operation is complete,
          use the `describe` command for the network.
        """,
    'EXAMPLES':
        """
          To update an network called ``my-network'' in region ``us-central1'' with
          a new label ``key1=value1'', run:

          $ {command} my-network  --region=us-central1 --update-labels=key1=value1

          To clear all labels, run:

          $ {command} my-network --region=us-central1 --clear-labels
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Bare Metal Solution network."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNetworkArgToParser(parser, positional=True)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    client = BmsClient()
    network = args.CONCEPTS.network.Parse()
    labels_update = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      orig_resource = client.GetNetwork(network)
      labels_update = labels_diff.Apply(
          client.messages.Network.LabelsValue,
          orig_resource.labels).GetOrNone()

    if not labels_diff.MayHaveUpdates():
      raise exceptions.NoConfigurationChangeError(
          'No configuration change was requested. Did you mean to include the '
          'flags `--update-labels` `--remove-labels` or `--clear-labels`?')

    op_ref = client.UpdateNetwork(
        network_resource=network, labels=labels_update)

    log.status.Print('Update request issued for: [{}]\nThis may take several '
                     'minutes to complete.'.format(network.Name()))

    return op_ref


Update.detailed_help = DETAILED_HELP
