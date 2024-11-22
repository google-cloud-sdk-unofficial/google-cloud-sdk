# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""The app create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import create_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

_DETAILED_HELP = {
    'DESCRIPTION': """\
        {description}
        """,
    'EXAMPLES': """\
        To create an app with region chosen interactively, run:

            $ {command}

        To create an app in the us-central region, run:

            $ {command} --region=us-central

        To create an app that with a user-managed service account, run:

            $ {command} --service-account=SERVICE_ACCOUNT
        """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an App Engine app within the current Google Cloud Project."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    create_util.AddAppCreateFlags(parser)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    if args.region:
      create_util.CreateApp(
          api_client,
          project,
          args.region,
          service_account=args.service_account)
    elif console_io.CanPrompt():
      create_util.CheckAppNotExists(api_client, project)
      create_util.CreateAppInteractively(
          api_client, project, service_account=args.service_account)
    else:
      raise create_util.UnspecifiedRegionError(
          'Prompts are disabled. Region must be specified either by the '
          '`--region` flag or interactively. Use `gcloud app regions '
          'list` to list available regions.')
    log.status.Print('Success! The app is now created. Please use '
                     '`gcloud app deploy` to deploy your first app.')


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Create an App Engine app within the current Google Cloud Project."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    create_util.AddAppCreateFlags(parser)

    parser.add_argument(
        '--ssl-policy',
        choices=['default', 'modern'],
        hidden=True,
        help='The app-level SSL policy to create the app with.',
    )

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    if args.region:
      create_util.CreateApp(
          api_client,
          project,
          args.region,
          service_account=args.service_account,
          ssl_policy=args.ssl_policy,
      )
    elif console_io.CanPrompt():
      create_util.CheckAppNotExists(api_client, project)
      create_util.CreateAppInteractively(
          api_client,
          project,
          service_account=args.service_account,
          ssl_policy=args.ssl_policy,
      )
    else:
      raise create_util.UnspecifiedRegionError(
          'Prompts are disabled. Region must be specified either by the '
          '`--region` flag or interactively. Use `gcloud app regions '
          'list` to list available regions.'
      )
    log.status.Print(
        'Success! The app is now created. Please use '
        '`gcloud app deploy` to deploy your first app.'
    )
