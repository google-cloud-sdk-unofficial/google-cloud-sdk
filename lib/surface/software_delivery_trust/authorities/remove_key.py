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
"""Remove a public key from a Software Delivery Trust verification authority."""

from googlecloudsdk.api_lib.software_delivery_trust import authorities
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.software_delivery_trust import flags


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveKey(base.Command):
  r"""Remove a public key from an existing Software Delivery Trust verification authority.

  ## EXAMPLES

  To remove a public key by its key ID from authority 'my-authority':

    $ {command} my-authority \
        --location=us-central1 \
        --key-id=key-2026-q4

  To remove a public key by its cryptographic fingerprint from authority 'my-authority':

    $ {command} my-authority \
        --location=us-central1 \
        --fingerprint="ni:///sha-256;f4OxZX_x_FO5LcGBSKHWXfwtSx-j1ncoSt3SABJtkGk"
  """

  @classmethod
  def Args(cls, parser):
    flags.AddAuthorityResourceArg(
        parser,
        'The authority to remove the public key from.',
        required=True,
        positional=True,
    )
    flags.AddRemoveKeyFlags(parser)

  def Run(self, args):
    client = authorities.AuthoritiesClient()
    authority_ref = args.CONCEPTS.authority.Parse()
    return client.RemoveKey(
        authority_ref,
        key_id=args.key_id,
        fingerprint=args.fingerprint,
    )
