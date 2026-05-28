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
"""Client for interaction with Data Products API CRUD DATAPLEX."""

from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.command_lib.iam import iam_util


def SetIamPolicy(data_product_ref, policy):
  """Set IAM Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule().DataplexProjectsLocationsDataProductsSetIamPolicyRequest(
      resource=data_product_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule().GoogleIamV1SetIamPolicyRequest(
          policy=policy
      ),
  )
  return dataplex_api.GetClientInstance().projects_locations_dataProducts.SetIamPolicy(
      set_iam_policy_req
  )


def GetIamPolicy(data_product_ref):
  """Get IAM Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule().DataplexProjectsLocationsDataProductsGetIamPolicyRequest(
      resource=data_product_ref.RelativeName()
  )
  return dataplex_api.GetClientInstance().projects_locations_dataProducts.GetIamPolicy(
      get_iam_policy_req
  )


def AddIamPolicyBinding(data_product_ref, member, role):
  """Add IAM policy binding request."""
  policy = GetIamPolicy(data_product_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role
  )
  return SetIamPolicy(data_product_ref, policy)


def RemoveIamPolicyBinding(data_product_ref, member, role):
  """Remove IAM policy binding request."""
  policy = GetIamPolicy(data_product_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return SetIamPolicy(data_product_ref, policy)


def SetIamPolicyFromFile(data_product_ref, policy_file):
  """Set IAM policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file, dataplex_api.GetMessageModule().GoogleIamV1Policy
  )
  return SetIamPolicy(data_product_ref, policy)
