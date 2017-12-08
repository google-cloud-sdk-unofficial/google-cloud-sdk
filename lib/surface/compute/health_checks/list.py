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
"""Command for listing health checks."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import exceptions


class List(base_classes.BaseLister):
  """List health checks."""

  @staticmethod
  def Args(parser):
    base_classes.BaseLister.Args(parser)

    protocol = parser.add_argument(
        '--protocol',
        help='The health check protocol to be listed. Default is all listed.')
    protocol.detailed_help = """\
        If protocol is specified, only health checks for that protocol are
        listed, and protocol-specific columns are added to the output. By
        default, health checks for all protocols are listed.
        """

  @property
  def service(self):
    return self.compute.healthChecks

  @property
  def resource_type(self):
    return 'healthChecks'

  def GetResources(self, args, errors):
    health_checks = lister.GetGlobalResources(
        service=self.service,
        project=self.project,
        filter_expr=self.GetFilterExpr(args),
        http=self.http,
        batch_url=self.batch_url,
        errors=errors)

    # TODO(user): Need to add protocol-specific columns. For example, if
    # --protocol http is used, we need to add columns like HOST, REQUEST_PATH,
    # etc. Need to wait for some work to be done by gsfowler@, then (according
    # to his comments in CL/97712492) we should do something like this:
    # Display() method:
    # def Format(self, args, unused_resource):
    #   if args.filter_on_http:
    #     return 'table(foo, bar, baz.http_special_field:label=HTTP_SPECIAL, ..)
    #   elif ...:
    #      ...
    #   else:
    #     return 'table(generic.field, bla, bla.bla, ...)'

    # If a protocol is specified, check that it is one we support, and convert
    # it to a number.
    protocol_value = None
    if args.protocol is not None:
      protocol_whitelist = [
          self.messages.HealthCheck.TypeValueValuesEnum.HTTP.number,
          self.messages.HealthCheck.TypeValueValuesEnum.HTTPS.number,
          self.messages.HealthCheck.TypeValueValuesEnum.HTTP2.number,
          self.messages.HealthCheck.TypeValueValuesEnum.TCP.number,
          self.messages.HealthCheck.TypeValueValuesEnum.SSL.number
          ]
      # Get the dictionary that maps strings to numbers, e.g. "HTTP" to 0.
      protocol_dict = self.messages.HealthCheck.TypeValueValuesEnum.to_dict()
      protocol_value = protocol_dict.get(args.protocol.upper())
      if protocol_value not in protocol_whitelist:
        raise exceptions.ToolException(
            'Invalid health check protocol ' + args.protocol + '.')

    for health_check in health_checks:
      if protocol_value is None or health_check.type.number == protocol_value:
        yield health_check


List.detailed_help = base_classes.GetGlobalListerHelp('health checks')
