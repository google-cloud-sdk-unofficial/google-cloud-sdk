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
"""Create endpoint verdict change request command."""

from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.api_lib.network_security.firewall_endpoints import wildfire_verdict_change_requests_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.command_lib.network_security import activation_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(base.CreateCommand):
  """Create a WildFire Verdict Change Request."""

  detailed_help = {
      'EXAMPLES': """\
        To create a WildFire Verdict Change Request with hash `deadbeef`, verdict `malware` and comment `bad file`, using full resource name for endpoint:

          $ {command} --endpoint=organizations/1234/locations/us-central1-a/firewallEndpoints/my-endpoint --hash=deadbeef --verdict=malware --comment="bad file"

        To create the same verdict change request for a project-level endpoint:

          $ {command} --endpoint=projects/my-project/locations/us-central1-a/firewallEndpoints/my-endpoint --hash=deadbeef --verdict=malware --comment="bad file"
        """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--hash',
        required=True,
        help='The hash of the file to submit a verdict change request for.',
    )
    parser.add_argument(
        '--verdict',
        required=True,
        help='The verdict being requested for the file.',
    )
    parser.add_argument(
        '--comment',
        required=True,
        help=(
            'The comment to be added to the verdict change request. Max length'
            ' 2048 characters.'
        ),
    )
    activation_flags.AddLocationArg(parser)
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
    endpoint_ref = args.CONCEPTS.endpoint.Parse()
    project_scoped = (
        endpoint_ref.concept_type.name
        == activation_flags.PROJECT_ENDPOINT_RESOURCE_COLLECTION
    )
    client = wildfire_verdict_change_requests_api.Client(
        self.ReleaseTrack(), project_scoped
    )
    # The API returns the created verdict change request directly rather than a
    # long-running operation.
    result = client.CreateVerdictChangeRequest(
        parent=endpoint_ref.result.RelativeName(),
        hash_val=args.hash,
        verdict=args.verdict,
        comment=args.comment,
    )
    log.CreatedResource(result.name, kind='WildFire verdict change request')
    return result
