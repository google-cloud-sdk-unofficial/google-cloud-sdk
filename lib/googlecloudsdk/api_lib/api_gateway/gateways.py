# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Client for interaction with Gateway CRUD on API Gateway API."""


from googlecloudsdk.api_lib.api_gateway import base
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.api_gateway import common_flags


class GatewayClient(base.BaseClient):
  """Client for gateway objects on Cloud API Gateway API."""

  def __init__(self, client=None, release_track=calliope_base.ReleaseTrack.GA):
    base.BaseClient.__init__(
        self,
        client=client,
        message_base='ApigatewayProjectsLocationsGateways',
        service_name='projects_locations_gateways',
        release_track=release_track,
    )
    self.DefineGet()
    self.DefineDelete()
    self.DefineList('gateways')
    self.DefineUpdate('apigatewayGateway')
    self.DefineIamPolicyFunctions()

  def Create(
      self,
      gateway_ref,
      api_config,
      display_name=None,
      labels=None,
      enable_streaming=None,
  ):
    """Creates a new gateway object.

    Args:
      gateway_ref: Resource, a resource reference for the gateway
      api_config: Resource, a resource reference for the gateway
      display_name: Optional display name
      labels: Optional cloud labels
      enable_streaming: Optional bool, enables streaming for the new gateway by
        setting streamingMode to STREAMING_MODE_ENABLED.

    Returns:
      Long running operation.
    """
    labels = common_flags.ProcessLabelsFlag(
        labels,
        self.messages.ApigatewayGateway.LabelsValue)

    gateway = self.messages.ApigatewayGateway(
        name=gateway_ref.RelativeName(),
        labels=labels,
        apiConfig=api_config.RelativeName(),
        displayName=display_name,
        )

    # streaming_mode is immutable and one-way: only set it when the user opts
    # in. An unset value means API Gateway selects the mode.
    if enable_streaming:
      # streaming_mode is GOOGLE_INTERNAL-restricted on v1/v1beta, so the enum
      # exists only on the v1alpha1 bindings. --enable-streaming is alpha-only,
      # but guard here for programmatic callers that reach this method with a
      # GA/beta (v1) client.
      streaming_mode_enum = getattr(
          self.messages.ApigatewayGateway, 'StreamingModeValueValuesEnum', None
      )
      if streaming_mode_enum is None:
        raise ValueError(
            'enable_streaming is only supported on the alpha release track;'
            ' the current API version does not define streaming_mode.'
        )
      gateway.streamingMode = streaming_mode_enum.STREAMING_MODE_ENABLED

    req = self.create_request(
        parent=gateway_ref.Parent().RelativeName(),
        gatewayId=gateway_ref.Name(),
        apigatewayGateway=gateway,
        )
    resp = self.service.Create(req)

    return resp
