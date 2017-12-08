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
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


LOG_LEVELS = ['critical', 'error', 'warning', 'info', 'debug', 'any']
FLEX_REQUESTS_LOG = 'nginx.requests'
STANDARD_REQUESTS_LOG = 'request_log'


class Read(base.Command):
  """Reads log entries for the current App Engine app."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('--service', '-s', help='Limit to specific service.')
    parser.add_argument('--version', '-v', help='Limit to specific version.')
    parser.add_argument('--limit', required=False, type=int,
                        default=200, help='Number of log entries to show.')
    parser.add_argument('--level', required=False, default='any',
                        choices=LOG_LEVELS,
                        help='Filter entries with severity equal to or higher '
                        'than a given level.')

    parser.add_argument('--logs',
                        required=False,
                        default=['stderr',
                                 'stdout',
                                 'crash.log',
                                 FLEX_REQUESTS_LOG,
                                 STANDARD_REQUESTS_LOG],
                        metavar='APP_LOG',
                        type=arg_parsers.ArgList(min_length=1),
                        help=('Filter entries from a particular set of logs. '
                              'Must be a comma-separated list of log names '
                              '(request_log, stdout, stderr, etc).'))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The list of log entries.
    """
    # Logging API filters later to be AND-joined
    filters = ['resource.type="gae_app"']

    # Argument handling
    if args.service:
      filters.append('resource.labels.module_id="{0}"'.format(args.service))
    if args.version:
      filters.append('resource.labels.version_id="{0}"'.format(args.version))
    if args.level != 'any':
      filters.append('severity>={0}'.format(args.level.upper()))

    printer = logs_util.LogPrinter()
    printer.RegisterFormatter(logs_util.FormatRequestLogEntry)
    printer.RegisterFormatter(logs_util.FormatAppEntry)

    lines = []
    log_id = lambda log_short: 'appengine.googleapis.com/%s' % log_short
    log_ids = sorted([log_id(log_short) for log_short in args.logs])
    # pylint: disable=g-builtin-op, For the .keys() method
    for entry in common.FetchLogs(log_filter=' AND '.join(filters),
                                  log_ids=sorted(log_ids),
                                  order_by='DESC',
                                  limit=args.limit):
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

          $ {command} --limit 10 --service=default

        To show only the logs from the request log for standard apps, run:

          $ {command} --logs=request_log

        To show only the logs from the request log for Flex apps, run:

          $ {command} --logs=nginx.requests
    """,
}
