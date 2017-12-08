# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command for spanner databases query."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.spanner import database_sessions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.core.resource import resource_printer


class Query(base.Command):
  """Cloud Spanner databases query."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.Instance(positional=False).AddToParser(parser)
    flags.Database().AddToParser(parser)
    parser.add_argument(
        '--sql',
        required=True,
        help='The SQL query to issue to the database. Cloud Spanner SQL is '
             'described at https://cloud.google.com/spanner/docs/query-syntax')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    session = database_sessions.Create(args.instance, args.database)
    try:
      return database_sessions.ExecuteSql(session, args.sql)
    finally:
      database_sessions.Delete(session)

  def Display(self, args, result):
    fields = [field.name for field in result.metadata.rowType.fields]
    table = ','.join(['row.slice({0}).join():label="{1}"'.format(i, f)
                      for i, f in enumerate(fields)])
    rows = [{'row': encoding.MessageToPyValue(row)} for row in result.rows]
    resource_printer.Print(rows, 'table({0})'.format(table))
