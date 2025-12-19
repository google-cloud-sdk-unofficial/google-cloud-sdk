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
"""Delete a single tenant HSM instance proposal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import resource_args
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
class Delete(base.DeleteCommand):
  r"""Delete a single tenant HSM instance proposal.

  ## EXAMPLES

  The following command deletes a single tenant HSM instance proposal:

  $ {command} projects/my-project/locations/us-east1/singleTenantHsmInstances/
  my_sthi/proposals/my_proposal
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
    if not single_tenant_hsm_instance_proposal_ref.Name():
      raise exceptions.InvalidArgumentException(
          'singletenanthsminstanceproposal',
          'singletenanthsminstanceproposal id must be non-empty.',
      )
    try:
      result = client.projects_locations_singleTenantHsmInstances_proposals.Delete(
          messages.CloudkmsProjectsLocationsSingleTenantHsmInstancesProposalsDeleteRequest(
              name=single_tenant_hsm_instance_proposal_ref.RelativeName()
          )
      )
      log.status.Print('Deleted proposal successfully.')
      return result
    except exceptions.HttpException as e:
      raise core_exceptions.Error('Failed to delete proposal: {}'.format(e))
