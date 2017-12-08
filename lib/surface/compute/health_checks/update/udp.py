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
"""Command for updating health checks."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import health_checks_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import exceptions as core_exceptions


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base_classes.ReadWriteCommand):

  """Update a UDP health check."""

  @staticmethod
  def Args(parser):
    health_checks_utils.AddUdpRelatedArgs(parser,
                                          request_and_response_required=False)
    health_checks_utils.AddProtocolAgnosticUpdateArgs(parser, 'UDP')

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
    # We do not support using 'update udp' with a health check of a
    # different protocol.
    if (existing_check.type !=
        self.messages.HealthCheck.TypeValueValuesEnum.UDP):
      raise core_exceptions.Error(
          'update udp subcommand applied to health check with protocol ' +
          existing_check.type.name)

    # Description and PortName are the only attributes that can be cleared by
    # passing in an empty string (but we don't want to set it to empty string).
    if args.description:
      description = args.description
    elif args.description is None:
      description = existing_check.description
    else:
      description = None

    if args.port_name:
      port_name = args.port_name
    elif args.port_name is None:
      port_name = existing_check.udpHealthCheck.portName
    else:
      port_name = None

    new_health_check = self.messages.HealthCheck(
        name=existing_check.name,
        description=description,
        type=self.messages.HealthCheck.TypeValueValuesEnum.UDP,
        udpHealthCheck=self.messages.UDPHealthCheck(
            request=args.request or existing_check.udpHealthCheck.request,
            response=args.response or existing_check.udpHealthCheck.response,
            port=args.port or existing_check.udpHealthCheck.port,
            portName=port_name),
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
                      or args.request
                      or args.response)
    if args.description is None and args.port_name is None and args_unset:
      raise exceptions.ToolException('At least one property must be modified.')

    # Check that request and response are not empty. It is acceptable for it to
    # be None.
    if args.request is not None and not args.request:
      raise exceptions.ToolException(
          '"request" field for UDP can not be empty.')
    if args.response is not None and not args.response:
      raise exceptions.ToolException(
          '"response" field for UDP can not be empty.')

    return super(Update, self).Run(args)


Update.detailed_help = {
    'brief': ('Update a UDP health check'),
    'DESCRIPTION': """\
        *{command}* is used to update an existing UDP health check. Only
        arguments passed in will be updated on the health check. Other
        attributes will remain unaffected.
        """,
}
