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
"""Command to register deployed application with App Hub."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.design_center import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.design_center import flags
from googlecloudsdk.core import log


_DETAILED_HELP = {
    'DESCRIPTION': (
        'Register deployed resources with an AppHub application using '
        'an Application Design Center application as source.'
    ),
    'EXAMPLES': """ \
          To register a deployed application with App Hub, using the application
          `my-application` in the space `my-space`, in the project `my-project`
          and location `us-central1`, run:

          $ {command} my-application --space=my-space --project=my-project \\
            --location=us-central1 --terraform-state='{"version":4, "resources": [...]}'

          To register a deployed application with App Hub, using a signed GCS URI
          for the Terraform state file, run:

          $ {command} my-application --space=my-space --project=my-project \\
            --location=us-central1 --tfstate-signed-gcs-uri=`https://storage.googleapis.com/my-bucket/tfstate.json?x-goog-signature=...`
          """,
    'API REFERENCE': """ \
        This command uses the designcenter/v1alpha API. The full documentation for
        this API can be found at:
        http://cloud.google.com/application-design-center/docs
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class Register(base.Command):
  """Register resources with a deployed application in App Hub."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddRegisterDeployedApplicationFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = utils.GetClientInstance(self.ReleaseTrack())
    messages = utils.GetMessagesModule(self.ReleaseTrack())
    application_ref = args.CONCEPTS.application.Parse()

    register_request = messages.RegisterDeployedApplicationRequest(
    )

    if args.terraform_state:
      register_request.terraformState = args.terraform_state
    elif args.tfstate_signed_gcs_uri:
      register_request.tfstateSignedGcsUri = args.tfstate_signed_gcs_uri

    if args.service_account:
      register_request.serviceAccount = args.service_account

    request = (
        messages.DesigncenterProjectsLocationsSpacesApplicationsRegisterRequest(
            name=application_ref.RelativeName(),
            registerDeployedApplicationRequest=register_request,
        )
    )

    op = client.projects_locations_spaces_applications.Register(
        request
    )

    if args.async_:
      log.status.Print('Registration started asynchronously.')
      return op

    return utils.WaitForOperationWithEmbeddedResult(
        client,
        op,
        'Waiting for registration to complete',
        max_wait_sec=1800,
        release_track=self.ReleaseTrack(),
    )

