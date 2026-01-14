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
"""Command to preview an application."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.api_lib.design_center import applications as apis
from googlecloudsdk.api_lib.design_center import utils
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.design_center import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


_DETAILED_HELP = {
    "DESCRIPTION": "Preview an application in a space.",
    "EXAMPLES": textwrap.dedent("""\
        To preview the application my-application in space my-space, project
    my-project and location us-central1, run:

        $ {command} my-application --space=my-space --project=my-project --location=us-central1

    Or run:

        $ {command} projects/my-project/locations/us-central1/spaces/my-space/applications/my-application

    To preview the application my-application in space my-space, project
    my-project and location us-central1 using a worker pool
    projects/my-project/locations/us-central1/workerPools/my-worker-pool, run:

        $ {command} my-application --space=my-space --project=my-project --location=us-central1 --worker-pool=projects/my-project/locations/us-central1/workerPools/my-worker-pool

    To preview the application my-application and create a new service account
    for the preview, run:

        $ {command} my-application --space=my-space --project=my-project --location=us-central1 --create-sa

    To preview the application my-application and create a new provided service account for the preview, run:

        $ {command} my-application --space=my-space --project=my-project --location=us-central1 --create-sa --service-account=my-service-account@my-project.iam.gserviceaccount.com

    To preview the application my-application and use a specific existing service account for the preview, run:

        $ {command} my-application --space=my-space --project=my-project --location=us-central1 --service-account=projects/my-project/serviceAccounts/my-service-account@my-project.iam.gserviceaccount.com


    To preview the application my-application in space my-space, project
    my-project and location us-central1 asynchronously, run:

        $ {command} my-application --space=my-space --project=my-project --location=us-central1 --async
        """),
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class Preview(base.Command):
  """Preview a Design Center application."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddApplicationResourceArg(parser, verb="to preview")
    flags.AddPreviewApplicationFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    release_track = self.ReleaseTrack()
    application_ref = args.CONCEPTS.application.Parse()
    app_client = apis.ApplicationsClient(release_track)
    short_app_name = application_ref.applicationsId
    log.status.Print('Request issued for: [%s]' % short_app_name)
    operation = app_client.PreviewApplication(
        name=application_ref.RelativeName(),
        worker_pool=args.worker_pool,
        service_account=args.service_account,
        create_sa=args.create_sa,
    )

    if args.async_:
      log.status.Print('Check operation [%s] for status.' % operation.name)
      return operation

    # Synchronous Polling Implementation
    utils.WaitForOperationWithEmbeddedResult(
        app_client.client,
        operation,
        message=f'Waiting for operation [{operation.name}] to complete',
        release_track=release_track,
        max_wait_sec=600,
    )
    # Operation successful
    log.status.Print('Preview of [%s] completed.' % short_app_name)
    return app_client.GetApplication(application_ref.RelativeName())


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.UniverseCompatible
class PreviewGa(Preview):
  """Preview a Design Center application."""
  pass
