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
"""gcloud dns outbound-endpoints describe command."""

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import resource_args


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  r"""Describes a Cloud DNS outbound endpoint.

  This command displays the details of a Cloud DNS outbound endpoint.

  ## EXAMPLES

  To describe an outbound endpoint `my-endpoint` in `us-east1`, run:

    $ {command} my-endpoint --location=us-east1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddOutboundEndpointResourceArg(
        parser, verb='to describe', api_version='v1'
    )

  def Run(self, args):
    api_version = 'v1'
    client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)

    endpoint_ref = args.CONCEPTS.outbound_endpoint.Parse()
    request = messages.DnsOutboundEndpointsGetRequest(
        name=endpoint_ref.RelativeName()
    )
    return client.outboundEndpoints.Get(request)
