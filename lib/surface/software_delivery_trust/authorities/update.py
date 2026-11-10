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
"""Update Software Delivery Trust verification authority command."""

from googlecloudsdk.api_lib.software_delivery_trust import authorities
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.software_delivery_trust import flags


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  r"""Update a Software Delivery Trust verification authority.

  ## EXAMPLES

  To update the description of authority 'my-authority' in location 'us-central1':

    $ {command} my-authority \
        --location=us-central1 \
        --description="Updated production signing authority"
  """

  @classmethod
  def Args(cls, parser):
    flags.AddAuthorityResourceArg(
        parser, 'The authority to update.', required=True, positional=True
    )
    parser.add_argument(
        '--description',
        help='Human-readable description of the authority.',
    )

  def Run(self, args):
    client = authorities.AuthoritiesClient()
    authority_ref = args.CONCEPTS.authority.Parse()
    return client.Update(
        authority_ref,
        description=args.description,
    )
