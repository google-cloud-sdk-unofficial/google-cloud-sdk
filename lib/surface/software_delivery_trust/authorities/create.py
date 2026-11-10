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
"""Create Software Delivery Trust verification authority command."""

from googlecloudsdk.api_lib.software_delivery_trust import authorities
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.software_delivery_trust import flags
from googlecloudsdk.command_lib.software_delivery_trust import util


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  r"""Create a Software Delivery Trust verification authority.

  An Authority represents a trusted verification identity, containing public keys
  used to verify attestations for software artifacts.

  ## EXAMPLES

  To create an empty authority 'my-authority' in location 'us-central1':

    $ {command} my-authority \
        --location=us-central1 \
        --description="Production GitHub Actions builder"

  To create an authority with an initial Cloud KMS public key:

    $ {command} my-authority \
        --location=us-central1 \
        --description="Authority backed by Cloud KMS asymmetric signing key" \
        --kms-key-version="projects/my-project/locations/us-central1/keyRings/my-ring/cryptoKeys/my-key/cryptoKeyVersions/1"

  To create an authority with an initial local PKIX public key file:

    $ {command} my-authority \
        --location=us-central1 \
        --description="Authority for CI/CD workload" \
        --key-id="v1" \
        --pkix-public-key-file="./public_key.pem" \
        --signature-algorithm=ec-sign-p256-sha256
  """

  @classmethod
  def Args(cls, parser):
    flags.AddAuthorityResourceArg(
        parser, 'The authority to create.', required=True, positional=True
    )
    parser.add_argument(
        '--description',
        help='Human-readable description of the authority.',
    )
    flags.AddKeyDefinitionFlags(parser, required=False)

  def Run(self, args):
    client = authorities.AuthoritiesClient()
    authority_ref = args.CONCEPTS.authority.Parse()
    public_key = util.BuildPublicKeyFromArgs(args, client.messages)
    public_keys = [public_key] if public_key else []
    return client.Create(
        authority_ref,
        description=args.description,
        public_keys=public_keys,
    )
