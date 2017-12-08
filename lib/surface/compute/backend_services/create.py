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

   There are separate alpha, beta, and GA command classes in this file.
"""

from googlecloudsdk.api_lib.compute import backend_services_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import flags


def _ResolvePort(args):
  if args.port:
    return args.port
  if args.protocol in ['HTTPS', 'SSL']:
    return 443
  # Default to port 80, which is used for HTTP and TCP.
  return 80


def _ResolvePortName(args):
  """Determine port name if one was not specified."""
  if args.port_name:
    return args.port_name

  if args.protocol == 'HTTPS':
    return 'https'
  if args.protocol == 'SSL':
    return 'ssl'
  if args.protocol == 'TCP':
    return 'tcp'

  return 'http'


def _ResolveProtocol(messages, args, default='HTTP'):
  return messages.BackendService.ProtocolValueValuesEnum(
      args.protocol or default)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(backend_services_utils.BackendServiceMutator):
  """Create a backend service."""

  @staticmethod
  def Args(parser):
    flags.GLOBAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    flags.AddDescription(parser)
    flags.AddHttpHealthChecks(parser)
    flags.AddHttpsHealthChecks(parser)
    flags.AddTimeout(parser)
    flags.AddPortName(parser)
    flags.AddProtocol(parser)
    flags.AddEnableCdn(parser, default=False)

  @property
  def method(self):
    return 'Insert'

  def _CreateBackendService(self, args):
    backend_services_ref = flags.GLOBAL_BACKEND_SERVICE_ARG.ResolveAsResource(
        args, self.resources,
        default_scope=compute_flags.ScopeEnum.GLOBAL)

    health_checks = backend_services_utils.GetHealthChecks(args, self)
    if not health_checks:
      raise exceptions.ToolException('At least one health check required.')

    enable_cdn = True if args.enable_cdn else None

    return self.messages.BackendService(
        description=args.description,
        name=backend_services_ref.Name(),
        healthChecks=health_checks,
        port=_ResolvePort(args),
        portName=_ResolvePortName(args),
        protocol=_ResolveProtocol(self.messages, args),
        timeoutSec=args.timeout,
        enableCDN=enable_cdn)

  def CreateGlobalRequests(self, args):
    request = self.messages.ComputeBackendServicesInsertRequest(
        backendService=self._CreateBackendService(args),
        project=self.project)

    return [request]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateGA):
  """Create a backend service."""

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    flags.AddDescription(parser)
    flags.AddHttpHealthChecks(parser)
    flags.AddHttpsHealthChecks(parser)
    flags.AddTimeout(parser)
    flags.AddPortName(parser)
    flags.AddProtocol(parser, default=None)

    # These are in beta
    flags.AddConnectionDrainingTimeout(parser)
    flags.AddEnableCdn(parser, default=False)
    flags.AddSessionAffinity(parser, internal_lb=True)
    flags.AddAffinityCookieTtl(parser)

    # These are added for alpha
    flags.AddHealthChecks(parser)

    flags.AddLoadBalancingScheme(parser)

  def CreateGlobalRequests(self, args):
    if args.load_balancing_scheme == 'INTERNAL':
      raise exceptions.ToolException(
          'Must specify --region for internal load balancer.')
    backend_service = self._CreateBackendService(args)
    if args.connection_draining_timeout is not None:
      backend_service.connectionDraining = self.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout)

    if args.enable_cdn:
      backend_service.enableCDN = args.enable_cdn

    if args.session_affinity is not None:
      backend_service.sessionAffinity = (
          self.messages.BackendService.SessionAffinityValueValuesEnum(
              args.session_affinity))
    if args.affinity_cookie_ttl is not None:
      backend_service.affinityCookieTtlSec = args.affinity_cookie_ttl

    request = self.messages.ComputeBackendServicesInsertRequest(
        backendService=backend_service,
        project=self.project)

    return [request]

  def CreateRegionalRequests(self, args):
    backend_services_ref = self.CreateRegionalReference(
        args.name, args.region, resource_type='regionBackendServices')
    backend_service = self._CreateRegionBackendService(args)
    if args.connection_draining_timeout is not None:
      backend_service.connectionDraining = self.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout)

    request = self.messages.ComputeRegionBackendServicesInsertRequest(
        backendService=backend_service,
        region=backend_services_ref.region,
        project=backend_services_ref.project)

    return [request]

  def _CreateRegionBackendService(self, args):
    health_checks = backend_services_utils.GetHealthChecks(args, self)
    if not health_checks:
      raise exceptions.ToolException('At least one health check required.')

    return self.messages.BackendService(
        description=args.description,
        name=args.name,
        healthChecks=health_checks,
        loadBalancingScheme=(
            self.messages.BackendService.LoadBalancingSchemeValueValuesEnum(
                args.load_balancing_scheme)),
        protocol=_ResolveProtocol(self.messages, args, default='TCP'),
        timeoutSec=args.timeout)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(CreateGA):
  """Create a backend service."""

  @staticmethod
  def Args(parser):
    flags.GLOBAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    flags.AddDescription(parser)
    flags.AddHttpHealthChecks(parser)
    flags.AddHttpsHealthChecks(parser)
    flags.AddTimeout(parser)
    flags.AddPortName(parser)
    flags.AddProtocol(parser)

    # These are added for beta
    flags.AddConnectionDrainingTimeout(parser)
    flags.AddEnableCdn(parser, default=False)
    flags.AddSessionAffinity(parser)
    flags.AddAffinityCookieTtl(parser)

  def CreateGlobalRequests(self, args):
    backend_service = self._CreateBackendService(args)

    if args.connection_draining_timeout is not None:
      backend_service.connectionDraining = self.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout)
    if args.session_affinity is not None:
      backend_service.sessionAffinity = (
          self.messages.BackendService.SessionAffinityValueValuesEnum(
              args.session_affinity))
    if args.session_affinity is not None:
      backend_service.affinityCookieTtlSec = args.affinity_cookie_ttl

    request = self.messages.ComputeBackendServicesInsertRequest(
        backendService=backend_service,
        project=self.project)

    return [request]


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
