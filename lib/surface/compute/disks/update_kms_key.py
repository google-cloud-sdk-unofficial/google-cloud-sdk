# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Command for updating the KMS key of a persistent disk."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import kms_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags

DETAILED_HELP = {
    'brief': 'Update the KMS key of a persistent disk.',
    'DESCRIPTION': """
        * {command} * updates the KMS key of a Compute Engine persistent disk
        by rotating it to the primary version of the key or to the primary
        version of a new KMS key.
    """,
    'EXAMPLES': """
        To rotate the KMS key of a disk named example-disk-1 to the primary version, run:

          $ {command} example-disk-1 --zone=us-central1-a

        To change the KMS key of a disk named example-disk-2 to a new KMS key named
        example-key in a key ring named example-key-ring in the global scope, run:

          $ {command} example-disk-2 --zone=us-central1-a --kms-key=example-key --kms-keyring=example-key-ring --kms-location=global
    """,
}


def _CommonArgs(parser):
  """Add arguments used for parsing in all command tracks."""
  disks_flags.MakeDiskArg(plural=False).AddArgument(parser)
  disks_flags.AddKmsKeyArg(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.UniverseCompatible
class UpdateKmsKey(base.Command):
  """Update the KMS key of a persistent disk."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  @classmethod
  def _GetApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def Run(self, args):
    """Issues request for updating the KMS key of a disk."""
    compute_holder = self._GetApiHolder()
    client = compute_holder.client
    messages = client.messages
    resources = compute_holder.resources

    disk_ref = disks_flags.MakeDiskArg(plural=False).ResolveAsResource(
        args, resources
    )

    kms_key_ref = kms_utils.MaybeGetKmsKey(args, messages, None)
    kms_key_name = kms_key_ref.kmsKeyName if kms_key_ref else None

    if disk_ref.Collection() == 'compute.disks':
      service = client.apitools_client.disks
      request = messages.ComputeDisksUpdateKmsKeyRequest(
          project=disk_ref.project,
          zone=disk_ref.zone,
          disk=disk_ref.Name(),
          diskUpdateKmsKeyRequest=messages.DiskUpdateKmsKeyRequest(
              kmsKeyName=kms_key_name
          ),
      )
      return client.MakeRequests([(service, 'UpdateKmsKey', request)])
    elif disk_ref.Collection() == 'compute.regionDisks':
      service = client.apitools_client.regionDisks
      request = messages.ComputeRegionDisksUpdateKmsKeyRequest(
          project=disk_ref.project,
          region=disk_ref.region,
          disk=disk_ref.Name(),
          regionDiskUpdateKmsKeyRequest=messages.RegionDiskUpdateKmsKeyRequest(
              kmsKeyName=kms_key_name
          ),
      )
      return client.MakeRequests([(service, 'UpdateKmsKey', request)])


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateKmsKeyBeta(UpdateKmsKey):
  """Update the KMS key of a persistent disk."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateKmsKeyAlpha(UpdateKmsKeyBeta):
  """Update the KMS key of a persistent disk."""


UpdateKmsKey.detailed_help = DETAILED_HELP
