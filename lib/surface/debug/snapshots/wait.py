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

"""Wait command for gcloud debug snapshots command group."""

import re

from googlecloudsdk.api_lib.debug import debug
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _MatchesIdOrRegexp(snapshot, ids, patterns):
  """Check if a snapshot matches any of the given IDs or regexps.

  Args:
    snapshot: Any debug snapshot object.
    ids: A set of strings to search for exact matches on snapshot ID.
    patterns: A list of regular expressions to match against the file:line
      location of the snapshot.
  Returns:
    True if the snapshot matches any ID or pattern.
  """
  if snapshot.id in ids:
    return True
  for p in patterns:
    if p.search(snapshot.location):
      return True
  return False


class Wait(base.Command):
  """Wait for debug snapshots to complete."""

  detailed_help = {
      'DESCRIPTION': """\
          This command waits for one or more snapshots on a Cloud Debugger debug
          target to become completed. A snapshot is considered completed either
          if there was an error setting the snapshot or if the snapshot was hit
          on an instance of the debug target.
      """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'id_or_location_regexp', nargs='+',
        help="""\
            A snapshot ID or a regular expression to match against snapshot
            locations. The command will wait for a snapshot with one of the
            given IDs, or any snapshot whose location (file:line) contains the
            regular expression, to complete.
        """)
    parser.add_argument(
        '--all', action='store_true', default=False,
        help="""\
            If set, wait for all the specified snapshots to complete, instead of
            waiting for any one of them to complete.
        """)
    parser.add_argument(
        '--all-users', action='store_true', default=False,
        help="""\
            If set, wait for matching snapshots from all users, rather than
            only the current user.
        """)
    parser.add_argument(
        '--timeout', default=5, type=int,
        help="""\
            Maximum number of seconds to wait for a snapshot to complete.
        """)

  def Run(self, args):
    """Run the wait command."""
    project_id = properties.VALUES.core.project.Get(required=True)
    debugger = debug.Debugger(project_id)
    debuggee = debugger.FindDebuggee(args.target)
    ids = set(args.id_or_location_regexp)
    patterns = [re.compile(r) for r in args.id_or_location_regexp]
    snapshots = [
        s for s in debuggee.ListBreakpoints(
            include_all_users=args.all_users,
            include_inactive=True)
        if _MatchesIdOrRegexp(s, ids, patterns)]
    all_ids = set([s.id for s in snapshots])
    explicit_ids = [i for i in args.id_or_location_regexp if i in all_ids]

    # Look for all explicitly-requested snapshots plus any matching snapshots
    # that are not completed. Completed snapshots which were not requested would
    # just be noise in the output.
    snapshots = [s for s in snapshots
                 if s.id in explicit_ids or not s.isFinalState]

    # Preserve the order of any explicitly-requested ids. Put the others in
    # any order.
    ids = explicit_ids + [s.id for s in snapshots if s.id not in explicit_ids]

    if not ids:
      self._is_partial = False
      return []

    if len(ids) == 1:
      log.status.Print('Waiting for 1 snapshot.')
    else:
      log.status.Print('Waiting for {0} snapshots.'.format(len(ids)))

    snapshots = debuggee.WaitForMultipleBreakpoints(ids, wait_all=args.all,
                                                    timeout=args.timeout)
    self._is_partial = args.all and len(snapshots) != len(ids)
    return snapshots

  def Collection(self):
    return 'debug.snapshots'

  def Epilog(self, resources_were_displayed):
    if not resources_were_displayed:
      log.status.Print('No snapshots completed before timeout')
    elif self._is_partial:
      log.status.Print('Partial results - Not all snapshots completed')

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
    fields.append('consoleViewUrl:label=VIEW')
    return 'table({0})'.format(','.join(fields))
