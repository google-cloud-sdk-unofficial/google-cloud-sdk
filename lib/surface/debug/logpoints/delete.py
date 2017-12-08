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

"""Delete command for gcloud debug logpoints command group."""

from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class Delete(base.DeleteCommand):
  """Delete debug logpoints.

  This command deletes logpoints from a Cloud Debugger debug target.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'id_or_location_regexp', metavar='(ID|LOCATION-REGEXP)', nargs='+',
        help="""\
            A logpoint ID or a regular expression to match against logpoint
            locations. The logpoint with the given ID, or all logpoints whose
            locations (file:line) contain the regular expression, will be
            deleted.
        """)
    parser.add_argument(
        '--all-users', action='store_true', default=False,
        help="""\
            If set, any location regexp will match logpoints from all users,
            rather than only logpoints created by the current user. This flag is
            not required when specifying the exact ID of a logpoint created by
            another user.
        """)
    parser.add_argument(
        '--include-inactive', action='store_true', default=False,
        help="""\
            If set, any location regexp will also match inactive logpoints,
            rather than only logpoints which have not expired. This flag is
            not required when specifying the exact ID of an inactive logpoint.
        """)

  def Run(self, args):
    """Run the delete command."""
    project_id = properties.VALUES.core.project.Get(required=True)
    debugger = debug.Debugger(project_id)
    debuggee = debugger.FindDebuggee(args.target)
    logpoints = debuggee.ListMatchingBreakpoints(
        args.id_or_location_regexp, include_all_users=args.all_users,
        include_inactive=args.include_inactive,
        restrict_to_type=debugger.LOGPOINT_TYPE)
    for s in logpoints:
      debuggee.DeleteBreakpoint(s.id)
    return logpoints

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
    fields.append('short_status():label="STATUS BEFORE DELETION"')
    return """
      [log=status,
       empty-legend="No logpoints matched the requested values",
       legend="Deleted Logpoints"]
      table({0})
    """.format(','.join(fields))
