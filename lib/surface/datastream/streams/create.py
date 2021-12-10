# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to create connection profiles for a datastream."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastream import streams
from googlecloudsdk.api_lib.datastream import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datastream import flags
from googlecloudsdk.command_lib.datastream import resource_args
from googlecloudsdk.command_lib.datastream.streams import flags as streams_flags

DESCRIPTION = ('Create a Datastream stream')
EXAMPLES = """\
    To create a stream with an Oracle source and Google Cloud Storage destination:

        $ {command} STREAM --location=us-central1 --display-name=my-stream --source-name=source --oracle-source-config=source_config.json --destination-name=destination --gcs-destination-config=destination_config.json --backfill-none

    To create a connection profile for Mysql with a backfill all strategy that contains some excluded objects:

        $ {command} STREAM --location=us-central1 --display-name=my-stream --source-name=source --mysql-source-config=source_config.json --destination-name=destination --gcs-destination-config=destination_config.json --backfill-all --mysql-excluded-objects=excluded_objects.json

   """


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Create(base.Command):
  """Create a Datastream stream."""
  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddStreamResourceArg(parser, 'to create')

    streams_flags.AddDisplayNameFlag(parser)
    streams_flags.AddBackfillStrategyGroup(parser)
    streams_flags.AddValidationGroup(parser)

    flags.AddLabelsCreateFlags(parser)

  def Run(self, args):
    """Create a Datastream stream.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    """
    stream_ref = args.CONCEPTS.stream.Parse()
    parent_ref = stream_ref.Parent().RelativeName()

    stream_client = streams.StreamsClient()
    result_operation = stream_client.Create(
        parent_ref, stream_ref.streamsId, args)

    client = util.GetClientInstance()
    messages = util.GetMessagesModule()
    resource_parser = util.GetResourceParser()

    operation_ref = resource_parser.Create(
        'datastream.projects.locations.operations',
        operationsId=result_operation.name,
        projectsId=stream_ref.projectsId,
        locationsId=stream_ref.locationsId)

    return client.projects_locations_operations.Get(
        messages.DatastreamProjectsLocationsOperationsGetRequest(
            name=operation_ref.operationsId))
