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

"""'logging saved_queries delete' command."""

from __future__ import absolute_import

import argparse

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': (
        """\
        Delete a saved query.
    """
    ),
    'EXAMPLES': (
        """\
        To delete a saved query in a project, run:

          $ {command} MY_QUERY_ID --project=MY_PROJECT_ID --location=global
    """
    ),
}


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Logging saved query.

  Deletes a saved query resource in Google Cloud Logging.
  """

  @staticmethod
  def Args(parser: argparse.ArgumentParser) -> None:
    """Registers flags for this command.

    Args:
      parser: An argparse.ArgumentParser object. The parser that will be used to
        parse the command line arguments.
    """
    parser.add_argument('ID', help='ID of the saved query to delete.')
    util.AddParentArgs(parser, 'saved query to delete')
    util.AddBucketLocationArg(
        parser, True, 'Location of the saved query to delete.'
    )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Deletes a saved query using the Logging API.

    Args:
      args: An argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      None.
    """
    messages = util.GetMessages()
    client = util.GetClient()

    saved_query_name = util.CreateResourceName(
        util.GetBucketLocationFromArgs(args), 'savedQueries', args.ID
    )

    client.projects_locations_savedQueries.Delete(
        messages.LoggingProjectsLocationsSavedQueriesDeleteRequest(
            name=saved_query_name
        )
    )

    log.DeletedResource(saved_query_name, 'saved query')


Delete.detailed_help = DETAILED_HELP
