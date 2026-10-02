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
"""Code that's shared between multiple ssl-policies subcommands."""

from googlecloudsdk.command_lib.iam import iam_util


def GetIamPolicy(ssl_policy_ref, client):
  """Gets the IAM policy for an SSL policy.

  Args:
    ssl_policy_ref: The SSL policy reference.
    client: The client.

  Returns:
    The IAM policy.
  """
  if ssl_policy_ref.Collection() == 'compute.regionSslPolicies':
    service = client.apitools_client.regionSslPolicies
    request = client.messages.ComputeRegionSslPoliciesGetIamPolicyRequest(
        resource=ssl_policy_ref.Name(),
        region=ssl_policy_ref.region,
        project=ssl_policy_ref.project,
    )
    return client.MakeRequests([(service, 'GetIamPolicy', request)])[0]
  service = client.apitools_client.sslPolicies
  request = client.messages.ComputeSslPoliciesGetIamPolicyRequest(
      resource=ssl_policy_ref.Name(), project=ssl_policy_ref.project
  )
  return client.MakeRequests([(service, 'GetIamPolicy', request)])[0]


def SetIamPolicy(ssl_policy_ref, client, policy):
  """Sets the IAM policy for an SSL policy.

  Args:
    ssl_policy_ref: The SSL policy reference.
    client: The client.
    policy: The IAM policy.

  Returns:
    The set IAM policy.
  """
  result = None
  if ssl_policy_ref.Collection() == 'compute.sslPolicies':
    service = client.apitools_client.sslPolicies
    request = client.messages.ComputeSslPoliciesSetIamPolicyRequest(
        resource=ssl_policy_ref.Name(),
        project=ssl_policy_ref.project,
        globalSetPolicyRequest=client.messages.GlobalSetPolicyRequest(
            policy=policy
        ),
    )
    result = client.MakeRequests([(service, 'SetIamPolicy', request)])[0]
  elif ssl_policy_ref.Collection() == 'compute.regionSslPolicies':
    service = client.apitools_client.regionSslPolicies
    request = client.messages.ComputeRegionSslPoliciesSetIamPolicyRequest(
        resource=ssl_policy_ref.Name(),
        region=ssl_policy_ref.region,
        project=ssl_policy_ref.project,
        regionSetPolicyRequest=client.messages.RegionSetPolicyRequest(
            policy=policy
        ),
    )
    result = client.MakeRequests([(service, 'SetIamPolicy', request)])[0]
  iam_util.LogSetIamPolicy(ssl_policy_ref.Name(), 'SSL policy')
  return result
