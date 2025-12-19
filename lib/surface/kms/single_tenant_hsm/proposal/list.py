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
"""List single tenant HSM instances proposals within a location."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import resource_args


@base.DefaultUniverseOnly
class List(base.ListCommand):
  r"""List single tenant HSM instance proposals within a single tenant HSM instance.

  ## EXAMPLES

  To list all single tenant HSM instance proposals in a single tenant instance
  using the single tenant HSM instance name `my_sthi` and the location
  `us-east1`:

  $ {command} my_sthi --location=us-east1

  To list all single tenant HSM instance proposals in a single tenant instance
  using the single tenant HSM instance name `my_sthi` and the location
  `us-east1` with the full single tenant HSM instance resource name:

  $ {command}
  projects/my-project/locations/us-east1/singleTenantHsmInstances/my_sthi
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsSingleTenantHsmInstanceResourceArgForKMS(
        parser, True, 'single_tenant_hsm_instance'
    )
    parser.display_info.AddFormat("""
       table(
         name,
         state,
         quorum_parameters.required_approver_count,
         expire_time)
    """)

  def Run(self, args):
    """List single tenant HSM instance proposals."""
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    location_ref = args.CONCEPTS.single_tenant_hsm_instance.Parse()
    request = messages.CloudkmsProjectsLocationsSingleTenantHsmInstancesProposalsListRequest(
        parent=location_ref.RelativeName(),
    )

    return list_pager.YieldFromList(
        client.projects_locations_singleTenantHsmInstances_proposals,
        request,
        field='singleTenantHsmInstanceProposals',
        limit=args.limit,
        batch_size=args.page_size,
        batch_size_attribute='pageSize',
    )
