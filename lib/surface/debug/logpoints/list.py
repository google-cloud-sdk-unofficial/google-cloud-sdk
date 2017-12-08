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


from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times


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
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        'id_or_location_regexp', metavar='(ID|LOCATION-REGEXP)', nargs='*',
        help="""\
            Zero or more logpoint IDs, resource identifiers, or regular
            expressions to match against logpoint locations. If present, only
            logpoints matching one or more of these values will be displayed.
        """)
    parser.add_argument(
        '--all-users', action='store_true', default=False,
        help="""\
            If set, display logpoints from all users, rather than only the
            current user.
        """)
    parser.add_argument(
        '--include-expired', action='store_true', default=False,
        help="""\
            If set, include logpoints which have expired and are no longer
            active.
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
    if not args.include_expired and logpoint.createTime:
      create_time = times.ParseDateTime(logpoint.createTime, tzinfo=times.UTC)
      age = times.Now(times.UTC) - create_time
      if age.days:
        return False
    return True

  def Run(self, args):
    """Run the list command."""
    project_id = properties.VALUES.core.project.Get(required=True)
    debugger = debug.Debugger(project_id)
    debuggee = debugger.FindDebuggee(args.target)
    return [
        l for l in debuggee.ListBreakpoints(
            args.id_or_location_regexp, include_all_users=args.all_users,
            include_inactive=args.include_expired,
            restrict_to_type=debugger.LOGPOINT_TYPE)
        if self._ShouldInclude(args, l)]

  def Collection(self):
    return 'debug.logpoints'
