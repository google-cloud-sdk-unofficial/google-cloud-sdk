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

"""List command for gcloud debug logpoints command group."""

import datetime
import re

import dateutil.parser

from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List debug logpoints."""

  detailed_help = {
      'DESCRIPTION': """\
          This command displays a list of the active debug logpoints for a
          Cloud Debugger debug target.
      """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'location_regexp', metavar='LOCATION-REGEXP', nargs='*',
        help="""\
            Zero or more logpoint location regular expressions. If present,
            only logpoints whose locations contain one or more of these
            expressions will be displayed.
        """)
    parser.add_argument(
        '--all-users', action='store_true', default=False,
        help="""\
            If set, display logpoints from all users, rather than only the
            current user.
        """)
    parser.add_argument(
        '--include-inactive', action='store_true', default=False,
        help="""\
            If set, include logpoints which are no longer active.
        """)

  def _ShouldInclude(self, args, logpoint):
    """Determines if a logpoint should be included in the output.

    Args:
      args: The command-line arguments.
      logpoint: a Breakpoint message desciribing a logpoint.
    Returns:
      True if the logpoint should be included based on the criteria in args.
    """
    # Exclude expired logpoints.
    if not args.include_inactive and logpoint.createTime:
      create_time = dateutil.parser.parse(logpoint.createTime)
      if not create_time.tzinfo:
        create_time.replace(tzinfo=dateutil.tz.tzutc())
      age = (datetime.datetime.now(dateutil.tz.tzutc()) - create_time)
      if age.days:
        return False

    # Check if the logpoint matches the location regular expressions.
    if not args.location_regexp:
      return True
    for pattern in args.location_regexp:
      if re.search(pattern, logpoint.location):
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
            include_inactive=args.include_inactive,
            restrict_to_type=debugger.LOGPOINT_TYPE)
        if self._ShouldInclude(args, l)]

  def Collection(self):
    return 'debug.logpoints'

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
    fields.append('logLevel:label=LEVEL')
    if args.include_inactive:
      fields.append('createTime')
    fields.append('short_status():label=STATUS')
    fields.append('condition')
    fields.append('log_message_format')
    return 'table({0})'.format(','.join(fields))
