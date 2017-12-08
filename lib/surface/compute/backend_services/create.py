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
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.core import log


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


def AddIapFlag(parser):
  iap_flag = flags.AddIap(parser)
  # TODO(b/34479878): It would be nice if the auto-generated help text were
  # a bit better so we didn't need to be quite so verbose here.
  iap_flag.detailed_help = """\
    Configure Identity Aware Proxy (IAP) service. You can configure IAP to be
    'enabled' or 'disabled' (default). If it is enabled you can provide values
    for 'oauth2-client-id' and 'oauth2-client-secret'. For example,
    '--iap=enabled,oauth2-client-id=foo,oauth2-client-secret=bar' will
    turn IAP on, and '--iap=disabled' will turn it off. See
    https://cloud.google.com/iap/ for more information about this feature.
    """


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base_classes.BaseAsyncMutator):
  """Create a backend service."""

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    flags.AddDescription(parser)
    flags.AddHealthChecks(parser)
    flags.AddHttpHealthChecks(parser)
    flags.AddHttpsHealthChecks(parser)
    flags.AddTimeout(parser)
    flags.AddPortName(parser)
    flags.AddProtocol(parser, default=None)
    flags.AddEnableCdn(parser, default=False)
    flags.AddSessionAffinity(parser, internal_lb=False)
    flags.AddAffinityCookieTtl(parser)
    flags.AddConnectionDrainingTimeout(parser)
    flags.AddLoadBalancingScheme(parser)

  @property
  def method(self):
    return 'Insert'

  def _CreateBackendService(self, args, backend_services_ref):
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

  def CreateGlobalRequests(self, args, backend_services_ref):
    if args.load_balancing_scheme == 'INTERNAL':
      raise exceptions.ToolException(
          'Must specify --region for internal load balancer.')
    backend_service = self._CreateBackendService(args, backend_services_ref)

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

  def CreateRegionalRequests(self, args, backend_services_ref):
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

  def _ApplyIapArgs(self, iap_arg, backend_service):
    if iap_arg is not None:
      backend_service.iap = backend_services_utils.GetIAP(iap_arg,
                                                          self.messages)
      if backend_service.iap.enabled:
        log.warning(backend_services_utils.IapBestPracticesNotice())
      if (backend_service.iap.enabled and backend_service.protocol is not
          self.messages.BackendService.ProtocolValueValuesEnum.HTTPS):
        log.warning(backend_services_utils.IapHttpWarning())

  def CreateRequests(self, args):
    ref = flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client))
    if ref.Collection() == 'compute.backendServices':
      self.global_request = True
    elif ref.Collection() == 'compute.regionBackendServices':
      self.global_request = False

    if self.global_request:
      return self.CreateGlobalRequests(args, ref)
    else:
      return self.CreateRegionalRequests(args, ref)

  def Format(self, args):
    return self.ListFormat(args)

  @property
  def resource_type(self):
    return 'backendServices'

  @property
  def service(self):
    if self.global_request:
      return self.compute.backendServices
    else:
      return self.compute.regionBackendServices


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateGA):
  """Create a backend service."""

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    flags.AddDescription(parser)
    flags.AddHealthChecks(parser)
    flags.AddHttpHealthChecks(parser)
    flags.AddHttpsHealthChecks(parser)
    flags.AddTimeout(parser)
    flags.AddPortName(parser)
    flags.AddProtocol(parser, default=None)
    flags.AddEnableCdn(parser, default=False)
    flags.AddCacheKeyIncludeProtocol(parser, default=True)
    flags.AddCacheKeyIncludeHost(parser, default=True)
    flags.AddCacheKeyIncludeQueryString(parser, default=True)
    flags.AddCacheKeyQueryStringList(parser)
    flags.AddSessionAffinity(parser, internal_lb=True)
    flags.AddAffinityCookieTtl(parser)
    flags.AddConnectionDrainingTimeout(parser)
    flags.AddLoadBalancingScheme(parser)
    AddIapFlag(parser)

  def CreateGlobalRequests(self, args, backend_services_ref):
    if args.load_balancing_scheme == 'INTERNAL':
      raise exceptions.ToolException(
          'Must specify --region for internal load balancer.')
    backend_service = self._CreateBackendService(args, backend_services_ref)
    if args.connection_draining_timeout is not None:
      backend_service.connectionDraining = self.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout)

    if args.enable_cdn:
      backend_service.enableCDN = args.enable_cdn

    cache_key_policy = self.messages.CacheKeyPolicy()
    backend_services_utils.ValidateCacheKeyPolicyArgs(args)
    backend_services_utils.UpdateCacheKeyPolicy(args, cache_key_policy)
    if (not args.cache_key_include_host or
        not args.cache_key_include_protocol or
        not args.cache_key_include_query_string or
        args.cache_key_query_string_blacklist is not None or
        args.cache_key_query_string_whitelist is not None):
      backend_service.cdnPolicy = self.messages.BackendServiceCdnPolicy(
          cacheKeyPolicy=cache_key_policy)

    if args.session_affinity is not None:
      backend_service.sessionAffinity = (
          self.messages.BackendService.SessionAffinityValueValuesEnum(
              args.session_affinity))
    if args.affinity_cookie_ttl is not None:
      backend_service.affinityCookieTtlSec = args.affinity_cookie_ttl

    self._ApplyIapArgs(args.iap, backend_service)

    request = self.messages.ComputeBackendServicesInsertRequest(
        backendService=backend_service,
        project=self.project)

    return [request]

  def CreateRegionalRequests(self, args, backend_services_ref):
    if (not args.cache_key_include_host or
        not args.cache_key_include_protocol or
        not args.cache_key_include_query_string or
        args.cache_key_query_string_blacklist is not None or
        args.cache_key_query_string_whitelist is not None):
      raise exceptions.ToolException(
          'Custom cache key flags cannot be used for regional requests.')
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
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    flags.AddDescription(parser)
    flags.AddHealthChecks(parser)
    flags.AddHttpHealthChecks(parser)
    flags.AddHttpsHealthChecks(parser)
    flags.AddTimeout(parser)
    flags.AddPortName(parser)
    flags.AddProtocol(parser, default=None)
    flags.AddEnableCdn(parser, default=False)
    flags.AddSessionAffinity(parser, internal_lb=True)
    flags.AddAffinityCookieTtl(parser)
    flags.AddConnectionDrainingTimeout(parser)
    flags.AddLoadBalancingScheme(parser)
    AddIapFlag(parser)

  def CreateGlobalRequests(self, args, backend_services_ref):
    if args.load_balancing_scheme == 'INTERNAL':
      raise exceptions.ToolException(
          'Must specify --region for internal load balancer.')
    backend_service = self._CreateBackendService(args, backend_services_ref)

    if args.connection_draining_timeout is not None:
      backend_service.connectionDraining = self.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout)
    if args.session_affinity is not None:
      backend_service.sessionAffinity = (
          self.messages.BackendService.SessionAffinityValueValuesEnum(
              args.session_affinity))
    if args.session_affinity is not None:
      backend_service.affinityCookieTtlSec = args.affinity_cookie_ttl

    self._ApplyIapArgs(args.iap, backend_service)

    request = self.messages.ComputeBackendServicesInsertRequest(
        backendService=backend_service,
        project=self.project)

    return [request]

  def CreateRegionalRequests(self, args, backend_services_ref):
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
