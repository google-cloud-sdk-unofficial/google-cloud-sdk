# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Describe a key."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Get metadata for a given key.

  Returns metadata for the given key.

  ## EXAMPLES

  The following command returns metadata for the key `frodo` within
  the keyring `fellowship` in the location `us-east1`:

    $ {command} frodo --keyring fellowship --location us-east1
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyResourceArgument(parser, 'to describe')

  def _DescribeResponse(self, args, resp):
    # blank out the attestation in the response.
    if resp.primary is not None:
      resp.primary.attestation = None
    return resp

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    crypto_key_ref = flags.ParseCryptoKeyName(args)
    if not crypto_key_ref.Name():
      raise exceptions.InvalidArgumentException('key',
                                                'key id must be non-empty.')
    resp = client.projects_locations_keyRings_cryptoKeys.Get(
        messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=crypto_key_ref.RelativeName()))
    return self._DescribeResponse(args, resp)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeALPHA(Describe):
  r"""Get metadata for a given key.

  Returns metadata for the given key.

  The optional flag `attestation-file` specifies file to write attestation
  object into. The attestation object helps the user assert the integrity and
  provenance of the crypto operation.

  ## EXAMPLES

  The following command returns metadata for the key `frodo` within
  the keyring `fellowship` in the location `us-east1`:

    $ {command} frodo \
    --keyring fellowship \
    --location us-east1 \
    --attestation-file /tmp/attesation.txt
  """

  @staticmethod
  def Args(parser):
    super(DescribeALPHA, DescribeALPHA).Args(parser)
    flags.AddAttesationFileFlag(parser)

  def _DescribeResponse(self, args, resp):
    if args.attestation_file and resp.primary.attestation:
      try:
        log.WriteToFileOrStdout(
            args.attestation_file,
            encoding.MessageToJson(resp.primary.attestation),
            overwrite=True,
            binary=False,
            private=True)
      except files.Error as e:
        raise exceptions.BadFileException(e)

    if resp.primary.attestation:
      # blank out the attestation in the response.
      resp.primary.attestation = None
    return resp
