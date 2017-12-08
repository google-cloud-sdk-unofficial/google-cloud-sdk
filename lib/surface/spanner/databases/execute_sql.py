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
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer


def _GetAdditionalProperty(properties, property_key):
  """Gets the value for the given key in a list of properties."""
  for prop in properties:
    if prop.key == property_key:
      if hasattr(prop, 'value'):
        return prop.value
      return 'Unknown'
  return 'Unknown'


def _DisplayAggregateStats(result, out):
  """Displays the aggregate stats for a Spanner SQL query."""
  format_str = ('table[box](total_elapsed_time, cpu_time, rows_returned, '
                'rows_scanned)')
  additional_properties = result.stats.queryStats.additionalProperties
  stats = {
      'total_elapsed_time':
          _GetAdditionalProperty(additional_properties, 'elapsed_time'),
      'cpu_time':
          _GetAdditionalProperty(additional_properties, 'cpu_time'),
      'rows_returned':
          _GetAdditionalProperty(additional_properties, 'rows_returned'),
      'rows_scanned':
          _GetAdditionalProperty(additional_properties, 'rows_scanned')
  }
  resource_printer.Print(stats, format_str, out=out)


def _HasAggregateStats(result):
  """Checks if the given results have information about aggregate statistics."""
  return hasattr(result, 'stats') and hasattr(
      result.stats, 'queryStats') and result.stats.queryStats is not None


def _DisplayQueryPlan(result, out):
  if _HasAggregateStats(result):
    _DisplayAggregateStats(result, out)
  # TODO(b/37238879): Pretty print the query plan.
  resource_printer.Print(result, 'yaml', out=out)


def _DisplayQueryResults(result, out):
  fields = [field.name for field in result.metadata.rowType.fields]
  table = ','.join([
      'row.slice({0}).join():label="{1}"'.format(i, f)
      for i, f in enumerate(fields)
  ])
  rows = [{'row': encoding.MessageToPyValue(row)} for row in result.rows]
  resource_printer.Print(rows, 'table({0})'.format(table), out=out)


class Query(base.Command):
  """Execute a read-only SQL query against a Cloud Spanner database."""

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

    query_mode_choices = {
        'NORMAL':
            'Returns only the query result, without any information about '
            'the query plan.',
        'PLAN': 'Returns only the query plan, without any result rows or '
                'execution statistics information.',
        'PROFILE':
            'Returns both the query plan and the execution statistics along '
            'with the result rows.'
    }

    parser.add_argument(
        '--query-mode',
        default='NORMAL',
        type=str.upper,
        choices=query_mode_choices,
        help='Mode in which the query must be processed.')

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
      return database_sessions.ExecuteSql(session, args.sql, args.query_mode)
    finally:
      database_sessions.Delete(session)

  def Display(self, args, result):
    if args.query_mode == 'NORMAL':
      _DisplayQueryResults(result, log.out)
    elif args.query_mode == 'PLAN':
      _DisplayQueryPlan(result, log.out)
    # Query mode is 'PROFILE'
    else:
      _DisplayQueryPlan(result, log.out)
      _DisplayQueryResults(result, log.status)
