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

"""Delete command for gcloud debug snapshots command group."""

from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class Delete(base.DeleteCommand):
  """Delete debug snapshots.

  This command deletes snapshots from a Cloud Debugger debug target.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'id_or_location_regexp', metavar='(ID|LOCATION-REGEXP)', nargs='+',
        help="""\
            A snapshot ID or a regular expression to match against snapshot
            locations. The snapshot with the given ID, or all snapshots whose
            locations (file:line) contain the regular expression, will be
            deleted.
        """)
    parser.add_argument(
        '--all-users', action='store_true', default=False,
        help="""\
            If set, matching snapshots from all users will be deleted, rather
            than only snapshots created by the current user.
        """)
    parser.add_argument(
        '--include-inactive', action='store_true', default=False,
        help="""\
            If set, also delete snapshots which have been completed. By default,
            only pending snapshots will be deleted.
        """)

  def Run(self, args):
    """Run the delete command."""
    project_id = properties.VALUES.core.project.Get(required=True)
    debugger = debug.Debugger(project_id)
    debuggee = debugger.FindDebuggee(args.target)
    snapshots = debuggee.ListMatchingBreakpoints(
        args.id_or_location_regexp, include_all_users=args.all_users,
        include_inactive=args.include_inactive,
        restrict_to_type=debugger.SNAPSHOT_TYPE)
    print 'Deleting snapshots: {0}\n----'.format(snapshots)
    for s in snapshots:
      debuggee.DeleteBreakpoint(s.id)
    return snapshots

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
    fields.append('location.format("{0}:{1}", path, line):label=LOCATION')
    fields.append('short_status():label="STATUS BEFORE DELETION"')
    return """
      [log=status,
       empty-legend="No matching snapshots were found",
       legend="Deleted Snapshots"]
      table({0})
    """.format(','.join(fields))
