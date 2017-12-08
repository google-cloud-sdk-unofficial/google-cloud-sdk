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
"""Command for updating health checks."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import health_checks_utils
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import exceptions as core_exceptions


class Update(base_classes.ReadWriteCommand):

  """Update a SSL health check."""

  @staticmethod
  def Args(parser):
    health_checks_utils.AddTcpRelatedUpdateArgs(parser)
    health_checks_utils.AddProtocolAgnosticUpdateArgs(parser, 'SSL')

  @property
  def service(self):
    return self.compute.healthChecks

  @property
  def resource_type(self):
    return 'healthChecks'

  def CreateReference(self, args):
    return self.CreateGlobalReference(
        args.name, resource_type='healthChecks')

  def GetGetRequest(self, args):
    """Returns a request for fetching the existing health check."""
    return (self.service,
            'Get',
            self.messages.ComputeHealthChecksGetRequest(
                healthCheck=self.ref.Name(),
                project=self.project))

  def GetSetRequest(self, args, replacement, existing):
    """Returns a request for updating the health check."""
    return (self.service,
            'Update',
            self.messages.ComputeHealthChecksUpdateRequest(
                healthCheck=self.ref.Name(),
                healthCheckResource=replacement,
                project=self.project))

  def Modify(self, args, existing_check):
    """Returns a modified HealthCheck message."""
    # We do not support using 'update ssl' with a health check of a
    # different protocol.
    if (existing_check.type !=
        self.messages.HealthCheck.TypeValueValuesEnum.SSL):
      raise core_exceptions.Error(
          'update ssl subcommand applied to health check with protocol ' +
          existing_check.type.name)

    # Description, PortName, Request, and Response are the only attributes that
    # can be cleared by passing in an empty string (but we don't want to set it
    # to an empty string).
    if args.description:
      description = args.description
    elif args.description is None:
      description = existing_check.description
    else:
      description = None

    if args.port_name:
      port_name = args.port_name
    elif args.port_name is None:
      port_name = existing_check.sslHealthCheck.portName
    else:
      port_name = None

    if args.request:
      request = args.request
    elif args.request is None:
      request = existing_check.sslHealthCheck.request
    else:
      request = None

    if args.response:
      response = args.response
    elif args.response is None:
      response = existing_check.sslHealthCheck.response
    else:
      response = None

    proxy_header = existing_check.sslHealthCheck.proxyHeader
    if args.proxy_header is not None:
      proxy_header = self.messages.SSLHealthCheck.ProxyHeaderValueValuesEnum(
          args.proxy_header)
    new_health_check = self.messages.HealthCheck(
        name=existing_check.name,
        description=description,
        type=self.messages.HealthCheck.TypeValueValuesEnum.SSL,
        sslHealthCheck=self.messages.SSLHealthCheck(
            request=request,
            response=response,
            port=args.port or existing_check.sslHealthCheck.port,
            portName=port_name,
            proxyHeader=proxy_header),
        checkIntervalSec=(args.check_interval or
                          existing_check.checkIntervalSec),
        timeoutSec=args.timeout or existing_check.timeoutSec,
        healthyThreshold=(args.healthy_threshold or
                          existing_check.healthyThreshold),
        unhealthyThreshold=(args.unhealthy_threshold or
                            existing_check.unhealthyThreshold),
    )
    return new_health_check

  def Run(self, args):
    health_checks_utils.CheckProtocolAgnosticArgs(args)

    args_unset = not (args.port
                      or args.check_interval
                      or args.timeout
                      or args.healthy_threshold
                      or args.unhealthy_threshold
                      or args.proxy_header)
    if (args.description is None and args.request is None and
        args.response is None and args.port_name is None and args_unset):
      raise exceptions.ToolException('At least one property must be modified.')

    return super(Update, self).Run(args)


Update.detailed_help = {
    'brief': ('Update a SSL health check'),
    'DESCRIPTION': """\
        *{command}* is used to update an existing SSL health check. Only
        arguments passed in will be updated on the health check. Other
        attributes will remain unaffected.
        """,
}
