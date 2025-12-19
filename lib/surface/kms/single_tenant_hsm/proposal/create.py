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
"""Create a single tenant HSM instance proposal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import pems
from googlecloudsdk.command_lib.kms import resource_args


@base.DefaultUniverseOnly
class Create(base.Command):
  r"""Create a single tenant HSM instance proposal.

  $ {command}
      my_stchi
      --location=us-central1 \
      --required-approver-count=1  \
      --two-factor-public-key-pems=public_key_1.pem,public_key_2.pem
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsSingleTenantHsmInstanceResourceArgForKMS(
        parser, True, 'single_tenant_hsm_instance'
    )
    parser.add_argument(
        '--operation-type',
        type=str,
        required=True,
        help=(
            'The type of operation for the single tenant HSM instance proposal.'
        ),
    )
    parser.add_argument(
        '--required-approver-count',
        type=int,
        required=False,
        help=(
            'The number of approvers required for the single tenant HSM'
            ' instance. This is the M value used for M of N quorum. Must be'
            ' greater than or equal to 1 and less than or equal to the total'
            ' approver count of the single tenant HSM instance minus 1. This'
            ' field is required for the register_2fa_keys operation type.'
        ),
    )
    parser.add_argument(
        '--two-factor-public-key-pems',
        type=arg_parsers.ArgList(),
        required=False,
        metavar='PEM_FILE_PATH',
        help=(
            'The PEM files containing the two factor public keys  2FA keys for'
            ' M of N quorum auth tenant HSM instance. This field is required'
            ' for register_2fa_keys operation type.'
        ),
    )
    parser.add_argument(
        '--member-public-key-pem',
        type=str,
        required=False,
        help=(
            'The PEM file containing the public key of the quorum member to'
            ' add or remove. This field is required for add_quorum_member and'
            ' remove_quorum_member operation types.'
        ),
    )
    parser.add_argument(
        '--single-tenant-hsm-instance-proposal-id',
        required=False,
        help=(
            'The ID to use for the single tenant HSM instance proposal, which'
            ' will become the final component of the single tenant HSM'
            ' instance resource name.'
        ),
    )

  def validate_required_approver_count(self, args, messages, sthi_ref):
    if args.required_approver_count is None:
      raise exceptions.BadArgumentException(
          '--required-approver-count',
          'The required approver count must be specified for'
          ' register_2fa_keys operation type.',
      )
    get_request = (
        messages.CloudkmsProjectsLocationsSingleTenantHsmInstancesGetRequest(
            name=sthi_ref.RelativeName(),
        )
    )
    client = cloudkms_base.GetClientInstance()
    sthi = client.projects_locations_singleTenantHsmInstances.Get(get_request)
    max_required_approver_count = sthi.quorumAuth.totalApproverCount - 1

    if (
        args.required_approver_count < 2
        or args.required_approver_count > max_required_approver_count
    ):
      raise exceptions.BadArgumentException(
          '--required-approver-count',
          'The required approver count must be between 2 and {}.'.format(
              max_required_approver_count
          ),
      )

  def public_key_pem_files_to_list(self, args):

    if args.two_factor_public_key_pems is None:
      raise exceptions.BadArgumentException(
          '--two-factor-public-key-pems',
          'The two factor public key pems must be specified for'
          ' register_2fa_keys operation type.',
      )
    pem_list = []
    for pem_file in args.two_factor_public_key_pems:
      try:
        pem_list.append(pems.GetPemPublicKey(pem_file))
      except Exception as e:
        raise exceptions.BadArgumentException(
            '--two-factor-public-key-pems',
            'Error while attempting to read file {} : {}'.format(pem_file, e),
        )
    return pem_list

  def CreateRequest(self, args):
    messages = cloudkms_base.GetMessagesModule()
    sthi_ref = args.CONCEPTS.single_tenant_hsm_instance.Parse()
    sthi_proposal_id = (
        args.single_tenant_hsm_instance_proposal_id
        if args.single_tenant_hsm_instance_proposal_id
        else None
    )

    req = messages.CloudkmsProjectsLocationsSingleTenantHsmInstancesProposalsCreateRequest(
        parent=sthi_ref.RelativeName(),
        singleTenantHsmInstanceProposal=messages.SingleTenantHsmInstanceProposal(),
        singleTenantHsmInstanceProposalId=sthi_proposal_id,
    )
    if args.operation_type == 'register_2fa_keys':
      self.validate_required_approver_count(args, messages, sthi_ref)
      pem_list = self.public_key_pem_files_to_list(args)
      req.singleTenantHsmInstanceProposal.registerTwoFactorAuthKeys = (
          messages.RegisterTwoFactorAuthKeys(
              requiredApproverCount=args.required_approver_count,
              twoFactorPublicKeyPems=pem_list,
          )
      )
    elif args.operation_type == 'disable_sthi':
      req.singleTenantHsmInstanceProposal.disableSingleTenantHsmInstance = (
          messages.DisableSingleTenantHsmInstance()
      )
    elif args.operation_type == 'enable_sthi':
      req.singleTenantHsmInstanceProposal.enableSingleTenantHsmInstance = (
          messages.EnableSingleTenantHsmInstance()
      )
    elif args.operation_type == 'delete_sthi':
      req.singleTenantHsmInstanceProposal.deleteSingleTenantHsmInstance = (
          messages.DeleteSingleTenantHsmInstance()
      )
    elif args.operation_type == 'add_quorum_member':
      if args.member_public_key_pem is None:
        raise exceptions.BadArgumentException(
            '--member-public-key-pem',
            'The member public key must be specified for'
            ' add_quorum_member operation type.',
        )
      pem = pems.GetPemPublicKey(args.member_public_key_pem)
      req.singleTenantHsmInstanceProposal.addQuorumMember = (
          messages.AddQuorumMember(twoFactorPublicKeyPem=pem)
      )
    elif args.operation_type == 'remove_quorum_member':
      if args.member_public_key_pem is None:
        raise exceptions.BadArgumentException(
            '--member-public-key',
            'The member public key must be specified for'
            ' remove_quorum_member operation type.',
        )
      pem = pems.GetPemPublicKey(args.member_public_key_pem)
      req.singleTenantHsmInstanceProposal.removeQuorumMember = (
          messages.RemoveQuorumMember(twoFactorPublicKeyPem=pem)
      )
    elif args.operation_type == 'refresh_sthi':
      req.singleTenantHsmInstanceProposal.refreshSingleTenantHsmInstance = (
          messages.RefreshSingleTenantHsmInstance()
      )
    else:
      raise exceptions.BadArgumentException(
          '--operation-type',
          'The operation type must be one of register_2fa_keys,'
          ' disable_sthi,'
          ' enable_sthi,'
          ' delete_sthi,'
          ' add_quorum_member,'
          ' remove_quorum_member, or'
          ' refresh_sthi.',
      )
    return req

  def Run(self, args):
    """Create a single tenant HSM instance."""
    client = cloudkms_base.GetClientInstance()

    operation = (
        client.projects_locations_singleTenantHsmInstances_proposals.Create(
            self.CreateRequest(args)
        )
    )

    return operation
