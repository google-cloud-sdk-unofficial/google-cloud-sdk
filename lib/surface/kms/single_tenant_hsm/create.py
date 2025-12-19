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
"""Create a single tenant HSM instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import resource_args


@base.DefaultUniverseOnly
class Create(base.Command):
  r"""Create a single tenant HSM instance.

  ## EXAMPLES

  The following command creates a single tenant HSM instance
  within the location `us-central1` with a total approver count of 3:

  $ {command} --location=us-central1 \
      --total-approver-count=3

  The following command creates a single tenant HSM instance within the location
  `us-central1` with a total approver count of 3, and the single tenant HSM
  instance ID `my_stchi`:

    $ {command} --location=us-central1 \
      --total-approver-count=3 \
      --single-tenant-hsm-instance-id=my_stchi
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsLocationResourceArgForKMS(parser, True, '--location')
    parser.add_argument(
        '--total-approver-count',
        type=int,
        required=True,
        help=(
            'The total number of approvers. This is the N value used for M of N'
            ' quorum auth. Must be greater than or equal to 3 and less than or'
            ' equal to 16.'
        ),
    )
    parser.add_argument(
        '--single-tenant-hsm-instance-id',
        type=str,
        required=False,
        help=(
            'Specify an ID for the single tenant HSM instance. It must be'
            ' unique within a location and match the regular expression'
            ' `[a-zA-Z0-9_-]{1,63}`.'
        ),
    )

  def CreateRequest(self, args):
    messages = cloudkms_base.GetMessagesModule()
    location_ref = args.CONCEPTS.location.Parse()
    parent = location_ref.RelativeName()
    if args.total_approver_count < 3 or args.total_approver_count > 16:
      raise exceptions.BadArgumentException(
          '--total-approver-count',
          'The total approver count must be between 3 and 16.',
      )
    stchi_id = (
        args.single_tenant_hsm_instance_id
        if args.single_tenant_hsm_instance_id
        else None
    )
    return (
        messages.CloudkmsProjectsLocationsSingleTenantHsmInstancesCreateRequest(
            parent=parent,
            singleTenantHsmInstanceId=stchi_id,
            singleTenantHsmInstance=messages.SingleTenantHsmInstance(
                quorumAuth=messages.QuorumAuth(
                    totalApproverCount=int(args.total_approver_count),
                ),
            ),
        )
    )

  def Run(self, args):
    """Create a single tenant HSM instance."""
    client = cloudkms_base.GetClientInstance()

    return client.projects_locations_singleTenantHsmInstances.Create(
        self.CreateRequest(args)
    )
