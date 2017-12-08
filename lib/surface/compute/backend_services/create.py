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
"""Command for creating backend services.

   There are separate alpha, beta, and GA command classes in this file.  The
   key differences are that each track passes different message modules for
   inferring options to --balancing-mode.
"""

from googlecloudsdk.api_lib.compute import backend_services_utils
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.third_party.apis.compute.alpha import compute_alpha_messages
from googlecloudsdk.third_party.apis.compute.beta import compute_beta_messages
from googlecloudsdk.third_party.apis.compute.v1 import compute_v1_messages


def _Args(parser, messages):
  """Common arguments to create commands for each release track."""
  backend_services_utils.AddUpdatableArgs(parser, messages)

  parser.add_argument(
      'name',
      help='The name of the backend service.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base_classes.BaseAsyncCreator):
  """Create a backend service."""

  @staticmethod
  def Args(parser):
    _Args(parser, compute_v1_messages)

  @property
  def service(self):
    return self.compute.backendServices

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'backendServices'

  def _CommonBackendServiceKwargs(self, args):
    """Prepare BackendService kwargs for fields common to all release tracks.

    Args:
      args: CLI args to translate to BackendService proto kwargs.

    Returns:
      A dictionary of keyword arguments to be passed to the BackendService proto
      constructor.
    """
    backend_services_ref = self.CreateGlobalReference(args.name)

    if args.port:
      port = args.port
    else:
      # Default to port 80, which is used for HTTP and TCP.
      port = 80
      if args.protocol in ['HTTPS', 'SSL']:
        port = 443

    if args.port_name:
      port_name = args.port_name
    else:
      # args.protocol == 'HTTP'
      port_name = 'http'
      if args.protocol == 'HTTPS':
        port_name = 'https'
      elif args.protocol == 'SSL':
        port_name = 'ssl'
      elif args.protocol == 'TCP':
        port_name = 'tcp'

    protocol = self.messages.BackendService.ProtocolValueValuesEnum(
        args.protocol)

    health_checks = backend_services_utils.GetHealthChecks(args, self)
    if not health_checks:
      raise exceptions.ToolException('At least one health check required.')

    return dict(
        description=args.description,
        healthChecks=health_checks,
        name=backend_services_ref.Name(),
        port=port,
        portName=port_name,
        protocol=protocol,
        timeoutSec=args.timeout)

  def CreateRequests(self, args):
    request = self.messages.ComputeBackendServicesInsertRequest(
        backendService=self.messages.BackendService(
            **self._CommonBackendServiceKwargs(args)),
        project=self.project)

    return [request]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateGA):
  """Create a backend service."""

  @staticmethod
  def AffinityOptions(backend_service):
    return sorted(backend_service.SessionAffinityValueValuesEnum.to_dict())

  @staticmethod
  def Args(parser):
    _Args(parser, compute_alpha_messages)

    enable_cdn = parser.add_argument(
        '--enable-cdn',
        action='store_true',
        default=None,  # Tri-valued, None => don't change the setting.
        help='Enable cloud CDN.')
    enable_cdn.detailed_help = """\
        Enable Cloud CDN for the backend service. Cloud CDN can cache HTTP
        responses from a backend service at the edge of the network, close to
        users.
        """

    health_checks = parser.add_argument(
        '--health-checks',
        type=arg_parsers.ArgList(min_length=1),
        metavar='HEALTH_CHECK',
        action=arg_parsers.FloatingListValuesCatcher(),
        help=('Specifies a list of health check objects for checking the '
              'health of the backend service.'))
    health_checks.detailed_help = """\
        Specifies a list of health check objects for checking the health of
        the backend service. Health checks need not be for the same protocol
        as that of the backend service.
        """

    session_affinity = parser.add_argument(
        '--session-affinity',
        choices=CreateAlpha.AffinityOptions(
            compute_alpha_messages.BackendService),
        default='none',
        type=lambda x: x.upper(),
        help='The type of session affinity to use.')
    session_affinity.detailed_help = """\
        The type of session affinity to use for this backend service.  Possible
        values are:

          * none: Session affinity is disabled.
          * client_ip: Route requests to instances based on the hash of the
            client's IP address.
          * generated_cookie: Route requests to instances based on the contents
            of the "GCLB" cookie set by the load balancer.
        """

    affinity_cookie_ttl = parser.add_argument('--affinity-cookie-ttl',
                                              type=int,
                                              default=0,
                                              help=("""\
        If session-affinity is set to "generated_cookie", this flag sets
        the TTL, in seconds, of the resulting cookie.
        """))
    affinity_cookie_ttl.detailed_helpr = """\
        If session-affinity is set to "generated_cookie", this flag sets
        the TTL, in seconds, of the resulting cookie.  A setting of 0
        indicates that the cookie should be transient.
    """

  def CreateRequests(self, args):
    kwargs = self._CommonBackendServiceKwargs(args)
    if args.enable_cdn is not None:
      kwargs['enableCDN'] = args.enable_cdn

    kwargs['sessionAffinity'] = (
        self.messages.BackendService.SessionAffinityValueValuesEnum(
            args.session_affinity))
    kwargs['affinityCookieTtlSec'] = args.affinity_cookie_ttl

    request = self.messages.ComputeBackendServicesInsertRequest(
        backendService=self.messages.BackendService(**kwargs),
        project=self.project)

    return [request]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(CreateGA):
  """Create a backend service."""

  @staticmethod
  def Args(parser):
    _Args(parser, compute_beta_messages)


CreateGA.detailed_help = {
    'DESCRIPTION': """
        *{command}* is used to create backend services. Backend
        services define groups of backends that can receive
        traffic. Each backend group has parameters that define the
        group's capacity (e.g., max CPU utilization, max queries per
        second, ...). URL maps define which requests are sent to which
        backend services.

        Backend services created through this command will start out
        without any backend groups. To add backend groups, use 'gcloud
        compute backend-services add-backend' or 'gcloud compute
        backend-services edit'.
        """,
}
CreateAlpha.detailed_help = CreateGA.detailed_help
CreateBeta.detailed_help = CreateGA.detailed_help
