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
"""Command for waiting until managed instance group becomes stable."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import time_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.core import log


class WaitUntilStable(base_classes.BaseCommand):
  """Waits until state of managed instance group is stable."""

  _TIME_BETWEEN_POLLS_SEC = 10
  _OPERATION_TYPES = ['abandoning', 'creating', 'deleting', 'rebooting',
                      'restarting', 'recreating', 'refreshing']

  @staticmethod
  def Args(parser):
    parser.add_argument('name',
                        help='Name of the managed instance group.')
    parser.add_argument('--timeout',
                        type=int,
                        help='Timeout in seconds for waiting '
                        'for group becoming stable.')
    utils.AddZoneFlag(
        parser,
        resource_type='managed instance group',
        operation_type='wait until stable')

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def Run(self, args):
    start = time_utils.CurrentTimeSec()
    group_ref = self.CreateZonalReference(args.name, args.zone)
    while True:
      responses, errors = self._GetResources(group_ref)
      if errors:
        utils.RaiseToolException(errors)
      if WaitUntilStable._IsGroupStable(responses[0]):
        break
      log.out.Print(WaitUntilStable._MakeWaitText(responses[0]))
      time_utils.Sleep(WaitUntilStable._TIME_BETWEEN_POLLS_SEC)

      if args.timeout and time_utils.CurrentTimeSec() - start > args.timeout:
        raise utils.TimeoutError('Timeout while waiting for group to become '
                                 'stable.')
    log.out.Print('Group is stable')

  @staticmethod
  def _IsGroupStable(group):
    return not any(getattr(group.currentActions, action, 0)
                   for action in WaitUntilStable._OPERATION_TYPES)

  @staticmethod
  def _MakeWaitText(group):
    """Creates text presented at each wait operation."""
    text = 'Waiting for group to become stable, current operations: '
    actions = []
    for action in WaitUntilStable._OPERATION_TYPES:
      action_count = getattr(group.currentActions, action, 0)
      if action_count > 0:
        actions.append('{0}: {1}'.format(action, action_count))
    return text + ','.join(actions)

  def _GetResources(self, group_ref):
    """Retrieves response with named ports."""
    request = self.service.GetRequestType('Get')(
        instanceGroupManager=group_ref.Name(),
        zone=group_ref.zone,
        project=self.project)

    errors = []
    results = list(request_helper.MakeRequests(
        requests=[(self.service, 'Get', request)],
        http=self.http,
        batch_url=self.batch_url,
        errors=errors,
        custom_get_requests=None))

    return results, errors
