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

"""Command for adding health checks to target pools."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.http_health_checks import (
    flags as http_health_check_flags)
from googlecloudsdk.command_lib.compute.target_pools import flags


class AddHealthChecks(base_classes.NoOutputAsyncMutator):
  """Add an HTTP health check to a target pool.

  *{command}* is used to add an HTTP health check
  to a target pool. Health checks are used to determine
  the health status of instances in the target pool. Only one
  health check can be attached to a target pool, so this command
  will fail if there as already a health check attached to the target
  pool. For more information on health checks and load balancing, see
  [](https://cloud.google.com/compute/docs/load-balancing-and-autoscaling/)
  """

  HEALTH_CHECK_ARG = None
  TARGET_POOL_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.HEALTH_CHECK_ARG = (
        http_health_check_flags.HttpHealthCheckArgumentForTargetPool('add to'))
    cls.HEALTH_CHECK_ARG.AddArgument(parser)
    cls.TARGET_POOL_ARG = flags.TargetPoolArgument(
        help_suffix=' to which to add the health check.')
    cls.TARGET_POOL_ARG.AddArgument(
        parser, operation_type='add health checks to')

  @property
  def service(self):
    return self.compute.targetPools

  @property
  def method(self):
    return 'AddHealthCheck'

  @property
  def resource_type(self):
    return 'targetPools'

  def CreateRequests(self, args):
    health_check_ref = self.HEALTH_CHECK_ARG.ResolveAsResource(
        args, self.resources)

    target_pool_ref = self.TARGET_POOL_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))

    request = self.messages.ComputeTargetPoolsAddHealthCheckRequest(
        region=target_pool_ref.region,
        project=self.project,
        targetPool=target_pool_ref.Name(),
        targetPoolsAddHealthCheckRequest=(
            self.messages.TargetPoolsAddHealthCheckRequest(
                healthChecks=[self.messages.HealthCheckReference(
                    healthCheck=health_check_ref.SelfLink())])))

    return [request]
