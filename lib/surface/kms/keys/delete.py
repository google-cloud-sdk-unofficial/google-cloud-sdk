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
"""A command to delete a key."""

import argparse

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.generated_clients.apis.cloudkms.v1 import cloudkms_v1_messages


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Delete(base.DeleteCommand):
  """Delete a key.

  The following command deletes key `frodo` within keyring `fellowship` and
  location `us-east1`:

    $ {command} frodo --location=us-east1 --keyring=fellowship
  """

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    flags.AddKeyResourceArgument(parser, 'to delete')

  def Run(
      self, args: argparse.Namespace
  ) -> cloudkms_v1_messages.Operation:
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    key_ref = flags.ParseCryptoKeyName(args)
    ck = client.projects_locations_keyRings_cryptoKeys
    return ck.Delete(
        messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysDeleteRequest(
            name=key_ref.RelativeName()
        )
    )
