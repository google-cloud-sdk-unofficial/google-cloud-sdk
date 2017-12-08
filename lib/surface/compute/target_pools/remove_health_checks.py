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

"""Command for removing health checks from target pools."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags


class RemoveHealthChecks(base_classes.NoOutputAsyncMutator):
  """Remove an HTTP health check from a target pool.

  *{command}* is used to remove an HTTP health check
  from a target pool. Health checks are used to determine
  the health status of instances in the target pool. For more
  information on health checks and load balancing, see
  [](https://cloud.google.com/compute/docs/load-balancing-and-autoscaling/)
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--http-health-check',
        help=('Specifies an HTTP health check object to remove from the '
              'target pool.'),
        metavar='HEALTH_CHECK',
        completion_resource='httpHealthChecks',
        required=True)

    flags.AddRegionFlag(
        parser,
        resource_type='target pool',
        operation_type='remove health checks from')

    parser.add_argument(
        'name',
        completion_resource='targetPools',
        help=('The name of the target pool from which to remove the '
              'health check.'))

  @property
  def service(self):
    return self.compute.targetPools

  @property
  def method(self):
    return 'RemoveHealthCheck'

  @property
  def resource_type(self):
    return 'targetPools'

  def CreateRequests(self, args):
    http_health_check_ref = self.CreateGlobalReference(
        args.http_health_check, resource_type='httpHealthChecks')

    target_pool_ref = self.CreateRegionalReference(args.name, args.region)
    request = self.messages.ComputeTargetPoolsRemoveHealthCheckRequest(
        region=target_pool_ref.region,
        project=self.project,
        targetPool=target_pool_ref.Name(),
        targetPoolsRemoveHealthCheckRequest=(
            self.messages.TargetPoolsRemoveHealthCheckRequest(
                healthChecks=[self.messages.HealthCheckReference(
                    healthCheck=http_health_check_ref.SelfLink())])))

    return [request]
