# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Command for getting a target pool's health."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.compute import flags


class GetHealth(base_classes.BaseCommand):
  """Get the health of instances in a target pool."""

  @staticmethod
  def Args(parser):
    flags.AddRegionFlag(
        parser,
        resource_type='target pool',
        operation_type='get health information for')

    parser.add_argument(
        'name',
        completion_resource='targetPools',
        help='The name of the target pool.')

  @property
  def service(self):
    return self.compute.targetPools

  @property
  def resource_type(self):
    return 'targetPoolInstanceHealth'

  def GetTargetPool(self):
    """Fetches the target pool resource."""
    errors = []
    objects = list(request_helper.MakeRequests(
        requests=[(self.service,
                   'Get',
                   self.messages.ComputeTargetPoolsGetRequest(
                       project=self.project,
                       region=self.target_pool_ref.region,
                       targetPool=self.target_pool_ref.Name()))],
        http=self.http,
        batch_url=self.batch_url,
        errors=errors,
        custom_get_requests=None))
    if errors:
      utils.RaiseToolException(
          errors,
          error_message='Could not fetch target pool:')
    return objects[0]

  def Run(self, args):
    """Returns a list of TargetPoolInstanceHealth objects."""
    self.target_pool_ref = self.CreateRegionalReference(
        args.name, args.region, resource_type='targetPools')
    target_pool = self.GetTargetPool()
    instances = target_pool.instances

    # If the target pool has no instances, we should return an empty
    # list.
    if not instances:
      return

    requests = []
    for instance in instances:
      request_message = self.messages.ComputeTargetPoolsGetHealthRequest(
          instanceReference=self.messages.InstanceReference(
              instance=instance),
          project=self.project,
          region=self.target_pool_ref.region,
          targetPool=self.target_pool_ref.Name())
      requests.append((self.service, 'GetHealth', request_message))

    errors = []
    resources = request_helper.MakeRequests(
        requests=requests,
        http=self.http,
        batch_url=self.batch_url,
        errors=errors,
        custom_get_requests=None)

    for resource in resources:
      yield resource

    if errors:
      utils.RaiseToolException(
          errors,
          error_message='Could not get health for some targets:')


GetHealth.detailed_help = {
    'brief': 'Get the health of instances in a target pool',
    'DESCRIPTION': """\
        *{command}* displays the health of instances in a target pool.
        """,
}
