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
"""Command to register App Hub application resources."""

from typing import Any
from argparse import Namespace
from argparse import ArgumentParser
import textwrap
from googlecloudsdk.api_lib.design_center import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.design_center import flags
from googlecloudsdk.core import log


_DETAILED_HELP = {
    'DESCRIPTION': (
        'Register App Hub application resources.'
    ),
    'EXAMPLES': textwrap.dedent("""\
      To register App Hub application resources in project `my-project` location `us-central1`, with apphub application `projects/my-project/locations/us-central1/applications/my-application` and tfstate signed GCS URI `my-tfstate-signed-gcs-uri`, run:

          $ {command} --project=my-project --location=us-central1 --apphub-application=projects/my-project/locations/us-central1/applications/my-application --tfstate-signed-gcs-uri=my-tfstate-signed-gcs-uri
          """),
    'API REFERENCE': textwrap.dedent("""\
        This command uses the designcenter/v1 API. The full documentation for
        this API can be found at:
        http://cloud.google.com/application-design-center/docs
        """),
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
@base.Hidden
@base.UniverseCompatible
class RegisterAppHubApplicationResources(base.Command):
  """Registration of App Hub application resources.

  Attributes:
    detailed_help: A dictionary with detailed help information for the command.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser: ArgumentParser)-> None:
    """Register flags for this command."""
    flags.AddRegisterAppHubApplicationResourcesFlags(parser)

  def Run(self, args: Namespace) -> Any:
    """This is what gets called when the user runs this command."""
    client = utils.GetClientInstance(self.ReleaseTrack())
    messages = utils.GetMessagesModule(self.ReleaseTrack())

    register_request_payload = messages.RegisterAppHubApplicationResourcesRequest(
        tfstateContent=args.tfstate_content,
        tfstateSignedGcsUri=args.tfstate_signed_gcs_uri,
        apphubApplication=args.apphub_application,
    )
    request = messages.DesigncenterProjectsLocationsSpacesRegisterAppHubApplicationResourcesRequest(
        parent=f'projects/{args.project}/locations/{args.location}',
        registerAppHubApplicationResourcesRequest=register_request_payload,
    )

    op = client.projects_locations_spaces.RegisterAppHubApplicationResources(
        request
    )

    if args.async_:
      log.status.Print('Registration started asynchronously.')
      return op

    response = utils.WaitForOperationWithEmbeddedResult(
        client,
        op,
        'Waiting for registration to complete',
        max_wait_sec=1800,
        release_track=self.ReleaseTrack(),
    )

    log.status.Print(
        'Registration completed for AppHub application'
    )

    if response.get('registeredResources'):
      log.status.Print('Successfully registered resources:')
      for res in response['registeredResources']:
        log.status.Print('- {0}'.format(res))

    if response.get('unregisteredResources'):
      log.warning('Failed to register resources:')
      for failed_res in response['unregisteredResources']:
        log.warning(
            '- Resource: %s, Error: %s',
            failed_res['deployedResource']['resourceId'],
            failed_res['reason'],
        )

    return response
