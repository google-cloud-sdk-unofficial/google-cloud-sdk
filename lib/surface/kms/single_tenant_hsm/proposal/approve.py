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
"""Approve a single tenant HSM instance proposal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ast

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import pems
from googlecloudsdk.command_lib.kms import resource_args
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


def tuple_list_type(arg):
  try:
    return ast.literal_eval(arg)
  except ValueError as e:
    raise exceptions.BadArgumentException(
        '--challenge_replies',
        'Error while attempting to parse challenge replies: {}'.format(e),
    )


def _parse_challenge_replies(messages, challenge_reply_tuples):
  """Parses file paths from tuples into a list of ChallengeReply messages."""
  challenge_replies = []
  if not challenge_reply_tuples:
    return challenge_replies

  for challenge_reply in challenge_reply_tuples:
    if not isinstance(challenge_reply, tuple) or len(challenge_reply) != 2:
      raise exceptions.BadArgumentException(
          'challenge replies',
          'Each challenge reply must be a tuple of (signed_challenge_file,'
          ' public_key_file).',
      )
    signed_challenge_file, public_key_file = challenge_reply

    if not signed_challenge_file:
      raise exceptions.BadArgumentException(
          'challenge replies',
          'signed_challenge_file must be specified.',
      )
    if not public_key_file:
      raise exceptions.BadArgumentException(
          'challenge replies',
          'public_key_file must be specified.',
      )

    try:
      public_key = pems.GetPemPublicKey(public_key_file)
    except Exception as e:
      raise exceptions.BadArgumentException(
          'challenge replies',
          'Error while attempting to read public key file {}: {}'.format(
              public_key_file, e
          ),
      )
    try:
      signed_challenge = files.ReadBinaryFileContents(signed_challenge_file)
    except Exception as e:
      raise exceptions.BadArgumentException(
          'challenge replies',
          'Error while attempting to read signed challenge file {}: {}'.format(
              signed_challenge_file, e
          ),
      )
    challenge_replies.append(
        messages.ChallengeReply(
            signedChallenge=signed_challenge,
            publicKeyPem=public_key,
        )
    )
  return challenge_replies


@base.DefaultUniverseOnly
class Approve(base.Command):
  r"""Approve a single tenant HSM instance proposal.

  ## EXAMPLES

  The following command approves a single tenant HSM instance proposal with
  quorum challenge replies:

  $ {command} projects/my-project/locations/us-east1/singleTenantHsmInstances/
  my_sthi/proposals/my_proposal \
  --quorum-challenge-replies="[('signed_challenge_1.txt','public_key_1.pem'),
  ('signed_challenge_2.txt','public_key_2.pem'),
  ('signed_challenge_3.txt','public_key_3.pem')]"

  To approve a proposal with required challenges and quorum challenges:

  $ {command} projects/my-project/locations/us-east1/singleTenantHsmInstances/
  my_sthi/proposals/my_proposal \
  --required-challenge-replies="[('required_challenge.txt','public_key_1.pem')]" \
  --quorum-challenge-replies="[('quorum_challenge_1.txt','public_key_2.pem'),
  ('quorum_challenge_2.txt','public_key_3.pem')]"
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsSingleTenantHsmInstanceProposalResourceArgForKMS(
        parser, True, 'single_tenant_hsm_instance_proposal'
    )
    quorum_group = parser.add_group(
        required=True, help='Approval payload for the proposal.'
    )
    quorum_group.add_argument(
        '--quorum-challenge-replies',
        type=tuple_list_type,
        help=(
            'The challenge replies to approve the proposal. Challenge replies '
            'can be sent across multiple requests. Each tuple should be '
            '("signed_challenge_file", "public_key_file").'
        ),
    )
    quorum_group.add_argument(
        '--required-challenge-replies',
        type=tuple_list_type,
        help=(
            'A list of tuples, each containing the file paths for a required '
            'challenge reply. Each tuple should be '
            '("signed_challenge_file", "public_key_file").'
        ),
    )

  def ApproveRequest(self, args):
    messages = cloudkms_base.GetMessagesModule()
    single_tenant_hsm_instance_proposal_ref = (
        args.CONCEPTS.single_tenant_hsm_instance_proposal.Parse()
    )
    kms_client = cloudkms_base.GetClientInstance()
    proposal = kms_client.projects_locations_singleTenantHsmInstances_proposals.Get(
        messages.CloudkmsProjectsLocationsSingleTenantHsmInstancesProposalsGetRequest(
            name=single_tenant_hsm_instance_proposal_ref.RelativeName()
        )
    )

    approve_request = messages.ApproveSingleTenantHsmInstanceProposalRequest()

    if proposal.quorumParameters is not None:
      if args.quorum_challenge_replies is None:
        raise exceptions.RequiredArgumentException(
            '--quorum-challenge-replies',
            '--quorum-challenge-replies must be specified for proposals'
            ' requiring quorum parameters.',
        )
      if args.required_challenge_replies is not None:
        raise exceptions.BadArgumentException(
            '--required-challenge-replies',
            'This argument cannot be used with proposals requiring quorum'
            ' parameters.',
        )
      challenge_replies = _parse_challenge_replies(
          messages, args.quorum_challenge_replies
      )
      approve_request.quorumReply = messages.QuorumReply(
          challengeReplies=challenge_replies
      )
    elif proposal.requiredActionQuorumParameters is not None:
      if (
          args.required_challenge_replies is None
          and args.quorum_challenge_replies is None
      ):
        raise exceptions.RequiredArgumentException(
            '--required-challenge-replies and --quorum-challenge-replies',
            'At least one of --required-challenge-replies and'
            ' --quorum-challenge-replies must be specified for proposals'
            ' requiring required action quorum parameters.',
        )
      required_challenge_replies = _parse_challenge_replies(
          messages, args.required_challenge_replies
      )
      quorum_challenge_replies = _parse_challenge_replies(
          messages, args.quorum_challenge_replies
      )
      approve_request.requiredActionQuorumReply = (
          messages.RequiredActionQuorumReply(
              requiredChallengeReplies=required_challenge_replies,
              quorumChallengeReplies=quorum_challenge_replies,
          )
      )
    else:
      raise core_exceptions.Error(
          'Unsupported or missing approval parameters in proposal: {}'.format(
              proposal.name
          )
      )

    req = messages.CloudkmsProjectsLocationsSingleTenantHsmInstancesProposalsApproveRequest(
        name=single_tenant_hsm_instance_proposal_ref.RelativeName(),
        approveSingleTenantHsmInstanceProposalRequest=approve_request,
    )
    return req

  def Run(self, args):
    """Approve a single tenant HSM instance proposal."""
    client = cloudkms_base.GetClientInstance()
    result = (
        client.projects_locations_singleTenantHsmInstances_proposals.Approve(
            self.ApproveRequest(args)
        )
    )
    if result is not Exception:
      log.status.Print('Approved proposal successfully.')
    return result
