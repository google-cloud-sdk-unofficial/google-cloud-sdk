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
"""List endpoint verdict change requests command."""

from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.api_lib.network_security.firewall_endpoints import wildfire_verdict_change_requests_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.command_lib.network_security import activation_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List WildFire Verdict Change Requests."""

  detailed_help = {
      'EXAMPLES': """\
        To list WildFire Verdict Change Requests for endpoint with full resource name `organizations/1234/locations/us-central1-a/firewallEndpoints/my-endpoint`, run:

          $ {command} --endpoint=organizations/1234/locations/us-central1-a/firewallEndpoints/my-endpoint
        """,
  }

  @classmethod
  def Args(cls, parser):
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
        group_help=(
            'The endpoint to which the verdict change request belongs.'
        ),
    )
    concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)

  def Run(self, args):
    client = wildfire_verdict_change_requests_api.Client(self.ReleaseTrack())
    endpoint_ref = args.CONCEPTS.endpoint.Parse()
    return client.ListVerdictChangeRequests(
        parent=endpoint_ref.result.RelativeName(),
        limit=args.limit,
        page_size=args.page_size,
    )
