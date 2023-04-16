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
"""Updates a Cloud NetApp Volumes KMS Config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.kms_configs import client as kmsconfigs_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.kms_configs import flags as kmsconfigs_flags
from googlecloudsdk.command_lib.util.args import labels_util

from googlecloudsdk.core import log


# TODO(b/239613419):
# Keep gcloud beta netapp group hidden until v1beta1 API stable
# also restructure release tracks that GA \subset BETA \subset ALPHA once
# BETA is public.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateAlpha(base.UpdateCommand):
  """Update a Cloud NetApp Volumes KMS Config."""

  detailed_help = {
      'DESCRIPTION': """\
          Updates a KMS (Key Management System) Config
          """,
      'EXAMPLES': """\
          The following command updates a KMS Config instance's description and KMS Key Ring in the default netapp/location

              $ {command} --description="new KMS ring" --kms-keyring=keyring2

          To update a KMS Config asynchronously, run the following command:

              $ {command} --async --description="new KMS ring" --kms-keyring-keyring2
          """,
  }

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  @staticmethod
  def Args(parser):
    kmsconfigs_flags.AddKMSConfigUpdateArgs(parser)

  def Run(self, args):
    """Update a Cloud NetApp Volumes KMS Config in the current project."""
    kmsconfig_ref = args.CONCEPTS.kms_config.Parse()
    client = kmsconfigs_client.KmsConfigsClient(self._RELEASE_TRACK)
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    orig_kmsconfig = client.GetKmsConfig(kmsconfig_ref)
    ## Update labels
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(
          client.messages.KmsConfig.LabelsValue, orig_kmsconfig.labels
      ).GetOrNone()
    else:
      labels = None
    kms_config = client.ParseUpdatedKmsConfig(
        orig_kmsconfig,
        crypto_key_name=orig_kmsconfig.cryptoKeyName,
        description=args.description,
        labels=labels,
    )

    updated_fields = []
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if (
        args.IsSpecified('update_labels')
        or args.IsSpecified('remove_labels')
        or args.IsSpecified('clear_labels')
    ):
      updated_fields.append('labels')
    update_mask = ','.join(updated_fields)

    result = client.UpdateKmsConfig(
        kmsconfig_ref, kms_config, update_mask, args.async_
    )
    if args.async_:
      command = 'gcloud {} netapp kms-configs list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the updated kms config by listing all kms'
          ' configs:\n  $ {} '.format(command)
      )
    return result
