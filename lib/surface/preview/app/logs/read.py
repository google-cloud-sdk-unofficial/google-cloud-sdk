# Copyright 2015 Google Inc. All Rights Reserved.
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
"""app logs read command."""

from googlecloudsdk.api_lib.app import logs_util
from googlecloudsdk.api_lib.logging import common
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


LOG_LEVELS = ['critical', 'error', 'warning', 'info', 'debug', 'any']


@base.Hidden
class Read(base.Command):
  """Reads log entries for the current App Engine app."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('--service', '-s', help='Limit to specific service.')
    parser.add_argument('--version', '-v', help='Limit to specific version.')
    parser.add_argument('--numlines', '-n', required=False, type=int,
                        default=200, help='Number of log entries to show.')
    parser.add_argument('--level', required=False, default='any',
                        help='Filter entries with severity equal to or higher '
                             'than a given level. Must be one of `{0}`.'
                        .format('|'.join(LOG_LEVELS)))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The list of log entries.
    """

    project = properties.VALUES.core.project.Get(required=True)

    # log_id -> formatter function. Note that log_id is NOT the same as logName
    formatters = {
        'appengine.googleapis.com/crash.log': logs_util.FormatAppEntry,
        'appengine.googleapis.com/stderr': logs_util.FormatAppEntry,
        'appengine.googleapis.com/stdout': logs_util.FormatAppEntry,
    }

    # Logging API filters later to be AND-joined
    filters = ['resource.type="gae_app"']

    # Argument handling
    if args.service:
      filters.append('resource.labels.module_id="{0}"'.format(args.service))
    if args.version:
      filters.append('resource.labels.version_id="{0}"'.format(args.version))
    if args.level:
      args.level = args.level.lower()
    if args.level not in LOG_LEVELS:
      raise calliope_exceptions.UnknownArgumentException('--level', args.level)
    if args.level != 'any':
      filters.append('severity>={0}'.format(args.level.upper()))

    printer = common.LogPrinter(project=project)
    for log_id, fn in formatters.iteritems():
      printer.RegisterFormatter(log_id, fn)

    lines = []
    # pylint: disable=g-builtin-op, For the .keys() method
    for entry in common.FetchLogs(log_filter=' AND '.join(filters),
                                  log_ids=sorted(formatters.keys()),
                                  order_by='DESC',
                                  limit=args.numlines):
      lines.append(printer.Format(entry))
    for line in reversed(lines):
      log.out.Print(line)

Read.detailed_help = {
    'DESCRIPTION': """\
        Display the latest log entries from stdout, stderr and crash log for the
        current Google App Engine app in a human readable format.
    """,
    'EXAMPLES': """\
        To display the latest entries for the current app, run:

          $ {command}

        To show only the entries with severity at `warning` or higher, run:

          $ {command} --level=warning

        To show only the entries with a specific version, run:

          $ {command} --version=v1

        To show only the 10 latest log entries for the default service, run:

          $ {command} -n 10 --service=default
    """,
}
