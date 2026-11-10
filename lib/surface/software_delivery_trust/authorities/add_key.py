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
"""Add a public key to a Software Delivery Trust verification authority."""

from googlecloudsdk.api_lib.software_delivery_trust import authorities
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.software_delivery_trust import flags
from googlecloudsdk.command_lib.software_delivery_trust import util


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddKey(base.Command):
  r"""Add a public key to an existing Software Delivery Trust verification authority.

  ## EXAMPLES

  To add a Cloud KMS public key to authority 'my-authority':

    $ {command} my-authority \
        --location=us-central1 \
        --kms-key-version="projects/my-project/locations/us-central1/keyRings/my-ring/cryptoKeys/my-key/cryptoKeyVersions/2"

  To add a local PKIX public key file to authority 'my-authority':

    $ {command} my-authority \
        --location=us-central1 \
        --pkix-public-key-file=my_key.pem \
        --signature-algorithm=ec-sign-p256-sha256 \
        --key-id=key-2026-q4
  """

  @classmethod
  def Args(cls, parser):
    flags.AddAuthorityResourceArg(
        parser,
        'The authority to add the public key to.',
        required=True,
        positional=True,
    )
    flags.AddKeyDefinitionFlags(parser, required=True)

  def Run(self, args):
    client = authorities.AuthoritiesClient()
    authority_ref = args.CONCEPTS.authority.Parse()
    public_key = util.BuildPublicKeyFromArgs(args, client.messages)
    return client.AddKey(authority_ref, public_key)
