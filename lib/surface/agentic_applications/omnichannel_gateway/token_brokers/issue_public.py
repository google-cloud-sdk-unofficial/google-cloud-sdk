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
"""Command for omnichannel-gateway token-brokers issue-public."""

from googlecloudsdk.api_lib.agentic_applications import token_brokers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.agentic_applications import util as agentic_utils
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class IssuePublic(base.Command):
  """Issue a public token for a given token broker.

  ## DESCRIPTION
  Issues a public token for the specified token broker. Public tokens are
  used for standard access. Returns the access token, expiration, and session
  details.

  ## EXAMPLES
  To issue a public token for a token broker with ID `my-token-broker` in
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
    parser.display_info.AddFormat('yaml')

  def Run(self, args):
    """Run token-brokers issue-public command."""
    token_broker_ref = args.CONCEPTS.token_broker_id.Parse()
    client = token_brokers.TokenBrokersClient()
    return client.IssuePublicToken(token_broker_ref)


