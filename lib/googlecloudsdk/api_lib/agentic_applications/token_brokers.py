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
"""API library for Omnichannel Token Brokers."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.agentic_applications import client as api_client
from googlecloudsdk.api_lib.util import apis


def GetClientInstance(version='v1alpha'):
  """Returns the apitools client instance for agenticapplications."""
  return apis.GetClientInstance('agenticapplications', version)


def GetMessagesModule(version='v1alpha'):
  """Returns the apitools messages module for agenticapplications."""
  return apis.GetMessagesModule('agenticapplications', version)


class TokenBrokersClient(object):
  """Client for Omnichannel Token Brokers service."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_omnichannelTokenBrokers

  def IssuePublicToken(
      self, token_broker_ref, refresh_token=None, grant_type=None
  ):
    """Calls IssuePublicToken RPC.

    Args:
      token_broker_ref: Resource reference to omnichannelTokenBroker.
      refresh_token: str, optional refresh token.
      grant_type: str, optional grant type.

    Returns:
      TokenBrokerIssueTokenResponse message.
    """
    req = self.messages.TokenBrokerIssueTokenRequest(
        name=token_broker_ref.RelativeName(),
        refreshToken=refresh_token,
    )
    if grant_type:
      grant_enum = (
          self.messages.TokenBrokerIssueTokenRequest.GrantTypeValueValuesEnum
      )
      req.grantType = grant_enum(grant_type)

    return self._service.IssuePublicToken(req)

  def IssueTrustedToken(self, token_broker_ref, trusted_fields=None):
    """Calls IssueTrustedToken RPC.

    Args:
      token_broker_ref: Resource reference to omnichannelTokenBroker.
      trusted_fields: dict or Struct object of trusted fields.

    Returns:
      TokenBrokerIssueTrustedTokenResponse message.
    """
    relative_name = token_broker_ref.RelativeName()
    url = f"{self.client.url.rstrip('/')}/v1alpha/{relative_name}:issueTrustedToken"

    body = {
        'name': token_broker_ref.RelativeName(),
    }
    if trusted_fields:
      body['trustedFields'] = trusted_fields

    # Note: We use a manual HTTP request here instead of apitools because
    # the generated GoogleProtobufStruct message wraps fields in a 'fields' key,
    # whereas the API expects a flattened JSON object for trustedFields
    # (standard google.protobuf.Struct behavior). Using apitools would require
    # custom codecs or lead to serialization mismatch.
    req_client = api_client.OmnichannelGatewayClient()
    response_dict = req_client.Request(
        'POST',
        url,
        body=body,
        error_msg='Failed to issue trusted token',
    )

    return encoding.DictToMessage(
        response_dict, self.messages.TokenBrokerIssueTrustedTokenResponse
    )
