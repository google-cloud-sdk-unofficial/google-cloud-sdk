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
"""Command for omnichannel-gateway token-brokers issue-secured."""

from googlecloudsdk.api_lib.agentic_applications import token_brokers
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.agentic_applications import util as agentic_utils
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class IssueSecured(base.Command):
  """Issue a secured token for a given token broker.

  ## DESCRIPTION
  Issues a secured token for the specified token broker. Secure tokens are
  used for higher privilege access or specific operations requiring stronger
  verification. You can provide trusted fields JSON to be embedded in the token.
  Returns the access token, expiration, and session details.

  ## EXAMPLES
  To issue a secured token for a token broker with ID `my-token-broker` in
  location `us`, run:

    $ {command} my-token-broker --project=my-project-id --location=us
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    concept_parsers.ConceptParser.ForResource(
        'token_broker_id',
        agentic_utils.GetTokenBrokerResourceSpec(),
        'token broker to issue token for.',
        required=True,
    ).AddToParser(parser)
    parser.add_argument(
        '--trusted-fields',
        type=arg_parsers.ArgJSON(),
        help='Trusted fields (as JSON) to include in the token.',
    )
    parser.display_info.AddFormat('yaml')

  def Run(self, args):
    """Run token-brokers issue-secured command."""
    token_broker_ref = args.CONCEPTS.token_broker_id.Parse()
    client = token_brokers.TokenBrokersClient()

    return client.IssueTrustedToken(
        token_broker_ref, trusted_fields=args.trusted_fields
    )
