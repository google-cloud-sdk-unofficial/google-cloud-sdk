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
"""Command to infer connections for a space."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.design_center import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.design_center import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': (
        'Infers connections for catalog and shared template revisions within a'
        ' space. If no URIs are provided, it processes all templates in the'
        ' space, but may fail if a shared template is unexpectedly missing.'
    ),
    'EXAMPLES': """ \
        To infer connections for a space named `my-space` in location `us-central1` and project `my-project`, run:

          $ {command} my-space --project=my-project --location=us-central1

        To infer connections for a space named `my-space` in location `us-central1` and project `my-project`, with specific catalog template revision URIs and using Gemini, run:

          $ {command} platform --project=my-project --location=us-central1 \\
            --catalog-template-revision-uris=projects/my-project/locations/us-central1/spaces/security/catalogs/security/templates/certificate-authority/revisions/rev1,projects/my-project/locations/us-central1/spaces/security/catalogs/security/templates/certificate-authority/revisions/rev2 \\
            --use-gemini

        To infer connections for a space using the full resource name, run:

          $ {command} projects/cloud-appcenter-e2e-testing/locations/us-central1/spaces/platform \\
            --catalog-template-revision-uris=projects/cloud-appcenter-e2e-testing/locations/us-central1/spaces/security/catalogs/security/templates/certificate-authority/revisions/rev1 \\
            --use-gemini
        """,
    'API REFERENCE': """ \
    This command uses the designcenter/v1alpha API. The full documentation for
    this API can be found at:
    http://cloud.google.com/application-design-center/docs
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class InferConnections(base.Command):
  """Infer connections for a space."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddInferConnectionsFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = utils.GetClientInstance(self.ReleaseTrack())
    messages = utils.GetMessagesModule(self.ReleaseTrack())

    space_ref = args.CONCEPTS.space.Parse()
    parent = space_ref.RelativeName()

    infer_connections_request_msg = messages.InferConnectionsRequest()

    if args.IsSpecified('catalog_template_revision_uris'):
      infer_connections_request_msg.catalogTemplateRevisionUris = (
          args.catalog_template_revision_uris
      )
    if args.use_gemini:
      infer_connections_request_msg.useGemini = args.use_gemini

    request = (
        messages.DesigncenterProjectsLocationsSpacesInferConnectionsRequest(
            name=parent, inferConnectionsRequest=infer_connections_request_msg
        )
    )

    operation = client.projects_locations_spaces.InferConnections(request)
    log.status.Print(
        'Infer connections request issued for: [{0}]'.format(space_ref.Name())
    )

    if args.async_:
      return operation

    response_dict = utils.WaitForOperationWithEmbeddedResult(
        client,
        operation,
        'Waiting for infer connections to complete',
        max_wait_sec=7200,
        release_track=self.ReleaseTrack(),
    )

    log.status.Print(
        'Finished inferring connections for space [{0}].'.format(
            space_ref.Name()
        )
    )
    return response_dict
