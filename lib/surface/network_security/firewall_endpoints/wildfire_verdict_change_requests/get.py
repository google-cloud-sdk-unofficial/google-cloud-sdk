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
"""Get endpoint verdict change request command."""

from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.api_lib.network_security.firewall_endpoints import wildfire_verdict_change_requests_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.command_lib.network_security import activation_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Get(base.DescribeCommand):
  """Get a WildFire Verdict Change Request."""

  detailed_help = {
      'EXAMPLES': """\
        To get a WildFire Verdict Change Request with name `req-123` and endpoint `organizations/1234/locations/us-central1-a/firewallEndpoints/my-endpoint`:

          $ {command} req-123 --endpoint=organizations/1234/locations/us-central1-a/firewallEndpoints/my-endpoint
        """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'NAME',
        help='Name of the verdict change request to get.',
    )
    api_version = activation_api.GetApiVersion(cls.ReleaseTrack())
    org_spec = activation_flags.OrgEndpointResourceSpec(api_version)
    project_spec = activation_flags.ProjectEndpointResourceSpec(api_version)
    resource_spec = multitype.MultitypeResourceSpec(
        'endpoint', org_spec, project_spec, allow_inactive=True
    )
    presentation_spec = presentation_specs.MultitypeResourcePresentationSpec(
        name='--endpoint',
        concept_spec=resource_spec,
        required=True,
        group_help='The endpoint to which the verdict change request belongs.',
    )
    concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)

  def Run(self, args):
    client = wildfire_verdict_change_requests_api.Client(self.ReleaseTrack())
    endpoint_ref = args.CONCEPTS.endpoint.Parse()
    request_name = (
        endpoint_ref.result.RelativeName()
        + '/wildfireVerdictChangeRequests/'
        + args.NAME
    )
    return client.GetVerdictChangeRequest(name=request_name)
