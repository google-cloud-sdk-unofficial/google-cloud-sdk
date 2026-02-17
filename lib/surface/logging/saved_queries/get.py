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

"""'logging saved_queries get' command."""

import argparse

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.generated_clients.apis.logging.v2 import logging_v2_messages as messages

DETAILED_HELP = {
    'DESCRIPTION': (
        """\
        Get a saved query.
    """
    ),
    'EXAMPLES': (
        """\
        To get a saved query in a project, run:

          $ {command} ID --project=PROJECT_ID --location=LOCATION
    """
    ),
}


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Get(base.Command):
  """Get a Logging saved query.

  Gets a saved query resource in Google Cloud Logging.
  """

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    """Registers flags for this command.

    Args:
      parser: An argparse.ArgumentParser object. The parser that will be used to
        parse the command line arguments.
    """
    parser.add_argument('ID', help='ID of the saved query to get.')
    util.AddParentArgs(parser, 'saved query to get')
    util.AddBucketLocationArg(
        parser, True, 'Location of the saved query to get.'
    )

  def Run(self, args: argparse.Namespace) -> messages.SavedQuery:
    """This is what gets called when the user runs this command.

    Gets a saved query using the Logging API.

    Args:
      args: An argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Saved query get operation.
    """
    client = util.GetClient()
    return client.projects_locations_savedQueries.Get(
        messages.LoggingProjectsLocationsSavedQueriesGetRequest(
            name=(
                f'{util.GetParentFromArgs(args)}/locations/{args.location}'
                f'/savedQueries/{args.ID}'
            ),
        )
    )


Get.detailed_help = DETAILED_HELP
