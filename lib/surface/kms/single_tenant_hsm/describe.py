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
"""Describe a single tenant HSM instance."""

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import resource_args


@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Get metadata for a single tenant HSM instance.

  Returns metadata for the given single tenant HSM instance.

    ## EXAMPLES

  The following command returns the metadata for the single tenant HSM instance
  with the name `my_sthi` in the location `us-east1`using the fully specified
  name:

    $ {command}
    projects/my-project/locations/us-east1/singleTenantHsmInstances/mysthi

  The following command returns the metadata for the singletenanthsm instance
  with the name `mysthi` in the location `us-east1` using the location and
  resource id:

    $ {command} mysthi --location=us-east1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsSingleTenantHsmInstanceResourceArgForKMS(
        parser, True, 'single_tenant_hsm_instance'
    )

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    sthi_ref = args.CONCEPTS.single_tenant_hsm_instance.Parse()
    if not sthi_ref.Name():
      raise exceptions.InvalidArgumentException(
          'single_tenant_hsm_instance',
          'single_tenant_hsm_instance id must be non-empty.',
      )
    return client.projects_locations_singleTenantHsmInstances.Get(
        messages.CloudkmsProjectsLocationsSingleTenantHsmInstancesGetRequest(
            name=sthi_ref.RelativeName()
        )
    )
