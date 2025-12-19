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
"""Executes a single tenant HSM proposal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import resource_args


@base.DefaultUniverseOnly
class Execute(base.Command):
  r"""Executes a single tenant HSM proposal.

  Executes a single tenant HSM proposal. The proposal must be in an approved
  state.

  ## EXAMPLES

  The following command executes a single tenant HSM proposal named
  `my_proposal` associated with the single tenant HSM instance `my_sthi`
  within the location `us-central1` with the fully specified name.

  $ {command}
  projects/my-project/locations/us-central1/singleTenantHsmInstances/
  my_sthi/proposals/my_proposal

  The following command executes a single tenant HSM proposal named
  `my_proposal` associated with the single tenant HSM instance `my_sthi`
  within the location `us-central1` using the location,
  single-tenant-hsm-instance, and proposal id.

  $ {command} my_proposal --location=us-central1
  --single_tenant_hsm_instance=my_sthi
  proposal_id=my_proposal
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsSingleTenantHsmInstanceProposalResourceArgForKMS(
        parser, True, 'single_tenant_hsm_instance_proposal'
    )

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    single_tenant_hsm_instance_proposal_ref = (
        args.CONCEPTS.single_tenant_hsm_instance_proposal.Parse()
    )

    req = messages.CloudkmsProjectsLocationsSingleTenantHsmInstancesProposalsExecuteRequest(
        name=single_tenant_hsm_instance_proposal_ref.RelativeName()
    )
    return client.projects_locations_singleTenantHsmInstances_proposals.Execute(
        req
    )
