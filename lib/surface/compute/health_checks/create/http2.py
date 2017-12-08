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
"""Command for creating HTTP2 health checks."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import health_checks_utils
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base_classes.BaseAsyncCreator):
  """Create a HTTP2 health check to monitor load balanced instances."""

  @staticmethod
  def Args(parser):
    health_checks_utils.AddHttpRelatedCreationArgs(parser)
    health_checks_utils.AddHttpRelatedResponseArg(parser)
    health_checks_utils.AddProtocolAgnosticCreationArgs(parser, 'HTTP2')

  @property
  def service(self):
    return self.compute.healthChecks

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'healthChecks'

  def CreateRequests(self, args):
    """Returns the request necessary for adding the health check."""

    health_check_ref = self.CreateGlobalReference(
        args.name, resource_type='healthChecks')
    proxy_header = self.messages.HTTP2HealthCheck.ProxyHeaderValueValuesEnum(
        args.proxy_header)
    request = self.messages.ComputeHealthChecksInsertRequest(
        healthCheck=self.messages.HealthCheck(
            name=health_check_ref.Name(),
            description=args.description,
            type=self.messages.HealthCheck.TypeValueValuesEnum.HTTP2,
            http2HealthCheck=self.messages.HTTP2HealthCheck(
                host=args.host,
                port=args.port,
                portName=args.port_name,
                requestPath=args.request_path,
                proxyHeader=proxy_header,
                response=args.response),
            checkIntervalSec=args.check_interval,
            timeoutSec=args.timeout,
            healthyThreshold=args.healthy_threshold,
            unhealthyThreshold=args.unhealthy_threshold,
        ),
        project=self.project)

    return [request]


Create.detailed_help = {
    'brief': ('Create a HTTP2 health check to monitor load balanced instances'),
    'DESCRIPTION': """\
        *{command}* is used to create a HTTP2 health check. HTTP2 health checks
        monitor instances in a load balancer controlled by a target pool. All
        arguments to the command are optional except for the name of the health
        check. For more information on load balancing, see
        [](https://cloud.google.com/compute/docs/load-balancing-and-autoscaling/)
        """,
}
