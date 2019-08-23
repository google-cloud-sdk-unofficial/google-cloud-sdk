# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for spanner databases sampledb."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.api_lib.spanner import database_sessions
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.spanner import resource_args
from googlecloudsdk.command_lib.spanner import sampledb_util
from googlecloudsdk.command_lib.spanner import write_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Sample(base.CreateCommand):
  """Create a sample Cloud Spanner database."""

  _GCS_BUCKET = 'gs://spanner_sample_datasets/hacker_news'
  _TABLES = ('comments', 'stories')
  _TABLE_CSV_FILES = (
      'hn_comments.csv',
      'hn_stories.csv',
  )
  _SCHEMA = 'schema'
  _BATCH_SIZE = 1100

  @staticmethod
  def Args(parser):
    """See base class."""

    resource_args.AddDatabaseResourceArg(parser, 'to create')
    parser.display_info.AddCacheUpdater(flags.DatabaseCompleter)

  def __init__(self, *args, **kwargs):
    super(Sample, self).__init__(*args, **kwargs)
    self._database = None
    self._instance = None

  def Run(self, args):
    """Creates a Sample Database and loads the sample dataset.

    Args:
      args: an argparse.Namespace. All the arguments that were provided to this
        command invocation.
    """
    self._database = args.CONCEPTS.database.Parse()
    self._instance = self._database.Parent()

    schema = sampledb_util.GetSchemaFromGCS(self._GCS_BUCKET, self._SCHEMA)

    self._CreateDatabase(args.database, schema)

    with progress_tracker.ProgressTracker('Loading data') as tracker:  # pylint: disable=unused-variable
      for table, table_file in zip(self._TABLES, self._TABLE_CSV_FILES):
        table_data = sampledb_util.ReadCSVFileFromGCS(self._GCS_BUCKET,
                                                      table_file)
        self._LoadData(table_data, table)

    self._PrintInstructions(args.database, args.instance)
    return

  def _CreateDatabase(self, database, schema):
    """Create the sample database.

    Args:
      database: String. The database name.
      schema: String. The schema used for the sample database.

    Returns:
      Get Request from the Await operation.
    """

    op = databases.Create(self._instance, database,
                          flags.SplitDdlIntoStatements([schema]))

    return database_operations.Await(op, 'Creating sample database')

  def _LoadData(self, table_data, table_name):
    """Load data for a specified table.

    Args:
      table_data: a 2D list containing data from a CSV File. Example...
        table_data[0] = ['1', 'Some name', 'Some value'] table_data[1] = ['2',
        'Some other name', 'Some value']
      table_name: String. The name of the table to insert into.
    """
    ddl = databases.GetDdl(self._database)
    table = write_util.Table.FromDdl(ddl, table_name)
    columns = table.GetColumnTypes()

    session_name = database_sessions.Create(self._database)
    session = resources.REGISTRY.ParseRelativeName(
        relative_name=session_name.name,
        collection='spanner.projects.instances.databases.sessions')

    mutation_batch = []
    for row in table_data:
      mutation = sampledb_util.CreateInsertMutationFromCSVRow(
          table, row, columns)
      mutation_batch.append(mutation)
      if len(mutation_batch) >= self._BATCH_SIZE:
        database_sessions.Commit(session, mutation_batch)
        del mutation_batch[:]

    #  Commit any remaining mutations
    if mutation_batch:
      database_sessions.Commit(session, mutation_batch)

    database_sessions.Delete(session)
    return

  def _PrintInstructions(self, database, instance):
    """Prints a series of instructions for querying and deleting the database.

    Args:
      database: A string representing the name of the database.
      instance: A string representing the name of the instance.
    """

    instructions = (
        'To start querying, issue:\n\n"gcloud spanner databases '
        'execute-sql {0} --instance={1} --sql=SQL"\n\nwhere SQL is the '
        'query you would like to use. Alternatively, you may follow this '
        'quickstart guide for queries using the GCP console.\n\n'
        'https://cloud.google.com/spanner/docs/quickstart-console#run_a_query'
        '\n\nIf you would like to delete the '
        'database, issue:\n\n"gcloud spanner databases delete {0} '
        '--instance={1}"\n').format(database, instance)

    log.status.Print(instructions)
    return
