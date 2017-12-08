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

"""List command for gcloud debug snapshots command group."""

import datetime
import re

import dateutil.parser

from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List debug snapshots."""

  detailed_help = {
      'DESCRIPTION': """\
          This command displays a list of the active debug snapshots for a
          Cloud Debugger debug target.
      """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'location_regexp', metavar='LOCATION-REGEXP', nargs='*',
        help="""\
            Zero or more snapshot location regular expressions. Only snapshots
            whose locations contain one or more of these expressions will be
            displayed.
        """)
    parser.add_argument(
        '--all-users', action='store_true', default=False,
        help="""\
            If set, display snapshots from all users, rather than only the
            current user.
        """)
    parser.add_argument(
        '--include-expired', action='store_true', default=False,
        help="""\
            If set, include snapshots which are no longer active.
        """)

  def _ShouldInclude(self, args, snapshot):
    """Determines if a snapshot should be included in the output.

    Args:
      args: The command-line arguments.
      snapshot: a Breakpoint message desciribing a snapshot.
    Returns:
      True if the snapshot should be included based on the criteria in args.
    """
    # Exclude expired snapshots.
    if not args.include_expired and snapshot.createTime:
      age = (datetime.datetime.now(dateutil.tz.tzutc()) -
             dateutil.parser.parse(snapshot.createTime))
      if age.days:
        return False

    # Check if the snapshot matches the location regular expressions.
    if not args.location_regexp:
      return True
    for pattern in args.location_regexp:
      if re.search(pattern, snapshot.location):
        return True
    return False

  def Run(self, args):
    """Run the list command."""
    project_id = properties.VALUES.core.project.Get(required=True)
    debugger = debug.Debugger(project_id)
    debuggee = debugger.FindDebuggee(args.target)
    return [
        l for l in debuggee.ListBreakpoints(
            include_all_users=args.all_users,
            include_inactive=args.include_expired,
            restrict_to_type=debugger.SNAPSHOT_TYPE)
        if self._ShouldInclude(args, l)]

  def Collection(self):
    return 'debug.snapshots'

  def Format(self, args):
    """Format for printing the results of the Run() method.

    Args:
      args: The arguments that command was run with.
    Returns:
      A format string
    """
    fields = ['id']
    if args.all_users:
      fields.append('userEmail:label=USER')
    fields.append('location')
    fields.append('short_status():label=STATUS')
    if args.include_expired:
      fields.append('createTime')
    fields.append('consoleViewUrl:label=VIEW')
    return 'table({0})'.format(','.join(fields))
