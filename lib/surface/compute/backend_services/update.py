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
"""Commands for updating backend services.

   There are separate alpha, beta, and GA command classes in this file.
"""

import copy

from googlecloudsdk.api_lib.compute import backend_services_utils
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.core import log


def AddIapFlag(parser):
  # TODO(b/34479878): It would be nice if the auto-generated help text were
  # a bit better so we didn't need to be quite so verbose here.
  flags.AddIap(
      parser,
      help="""\
      Change the Identity Aware Proxy (IAP) service configuration for the
      backend service. You can set IAP to 'enabled' or 'disabled', or modify
      the OAuth2 client configuration (oauth2-client-id and
      oauth2-client-secret) used by IAP. If any fields are unspecified, their
      values will not be modified. For instance, if IAP is enabled,
      '--iap=disabled' will disable IAP, and a subsequent '--iap=enabled' will
      then enable it with the same OAuth2 client configuration as the first
      time it was enabled. See
      https://cloud.google.com/iap/ for more information about this feature.
      """)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGA(base_classes.ReadWriteCommand):
  """Update a backend service."""

  def __init__(self, *args, **kwargs):
    super(UpdateGA, self).__init__(*args, **kwargs)
    self.ref = None

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    flags.AddDescription(parser)
    flags.AddHealthChecks(parser)
    flags.AddHttpHealthChecks(parser)
    flags.AddHttpsHealthChecks(parser)
    flags.AddTimeout(parser, default=None)
    flags.AddPortName(parser)
    flags.AddProtocol(parser, default=None)
    flags.AddEnableCdn(parser, default=None)
    flags.AddSessionAffinity(parser, internal_lb=True)
    flags.AddAffinityCookieTtl(parser)
    flags.AddConnectionDrainingTimeout(parser)

  @property
  def service(self):
    if self.regional:
      return self.compute.regionBackendServices
    return self.compute.backendServices

  @property
  def resource_type(self):
    if self.regional:
      return 'regionBackendServices'
    return 'backendServices'

  def CreateReference(self, args):
    # TODO(b/35133484): remove once base classes are refactored away
    if not self.ref:
      self.ref = flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
          args,
          self.resources,
          scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client))
      self.regional = self.ref.Collection() == 'compute.regionBackendServices'
    return self.ref

  def GetGetRequest(self, args):
    if self.regional:
      return (
          self.service,
          'Get',
          self.messages.ComputeRegionBackendServicesGetRequest(
              project=self.project,
              region=self.ref.region,
              backendService=self.ref.Name()))
    return (
        self.service,
        'Get',
        self.messages.ComputeBackendServicesGetRequest(
            project=self.project,
            backendService=self.ref.Name()))

  def GetSetRequest(self, args, replacement, _):
    if self.regional:
      return (
          self.service,
          'Update',
          self.messages.ComputeRegionBackendServicesUpdateRequest(
              project=self.project,
              region=self.ref.region,
              backendService=self.ref.Name(),
              backendServiceResource=replacement))

    return (
        self.service,
        'Update',
        self.messages.ComputeBackendServicesUpdateRequest(
            project=self.project,
            backendService=self.ref.Name(),
            backendServiceResource=replacement))

  def Modify(self, args, existing):
    replacement = copy.deepcopy(existing)

    if args.connection_draining_timeout is not None:
      replacement.connectionDraining = self.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout)

    if args.description:
      replacement.description = args.description
    elif args.description is not None:
      replacement.description = None

    health_checks = backend_services_utils.GetHealthChecks(args, self)
    if health_checks:
      replacement.healthChecks = health_checks

    if args.timeout:
      replacement.timeoutSec = args.timeout

    if args.port:
      replacement.port = args.port

    if args.port_name:
      replacement.portName = args.port_name

    if args.protocol:
      replacement.protocol = (self.messages.BackendService
                              .ProtocolValueValuesEnum(args.protocol))

    if args.enable_cdn is not None:
      replacement.enableCDN = args.enable_cdn

    if args.session_affinity is not None:
      replacement.sessionAffinity = (
          self.messages.BackendService.SessionAffinityValueValuesEnum(
              args.session_affinity))

    if args.affinity_cookie_ttl is not None:
      replacement.affinityCookieTtlSec = args.affinity_cookie_ttl

    return replacement

  def ValidateArgs(self, args):
    if not any([
        args.affinity_cookie_ttl is not None,
        args.connection_draining_timeout is not None,
        args.description is not None,
        args.enable_cdn is not None,
        args.health_checks,
        args.http_health_checks,
        args.https_health_checks,
        args.port,
        args.port_name,
        args.protocol,
        args.session_affinity is not None,
        args.timeout is not None,
    ]):
      raise exceptions.ToolException('At least one property must be modified.')

  def Run(self, args):
    self.ValidateArgs(args)
    self.CreateReference(args)

    return super(UpdateGA, self).Run(args)

  def _ApplyIapArgs(self, iap_arg, existing, replacement):
    if iap_arg is not None:
      existing_iap = existing.iap
      replacement.iap = backend_services_utils.GetIAP(
          iap_arg, self.messages, existing_iap_settings=existing_iap)
      if replacement.iap.enabled and not (existing_iap and
                                          existing_iap.enabled):
        log.warning(backend_services_utils.IapBestPracticesNotice())
      if (replacement.iap.enabled and replacement.protocol is not
          self.messages.BackendService.ProtocolValueValuesEnum.HTTPS):
        log.warning(backend_services_utils.IapHttpWarning())


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateGA):
  """Update a backend service."""

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    flags.AddDescription(parser)
    flags.AddHealthChecks(parser)
    flags.AddHttpHealthChecks(parser)
    flags.AddHttpsHealthChecks(parser)
    flags.AddTimeout(parser, default=None)
    flags.AddPortName(parser)
    flags.AddProtocol(parser, default=None)

    flags.AddConnectionDrainingTimeout(parser)
    flags.AddEnableCdn(parser, default=None)
    flags.AddCacheKeyIncludeProtocol(parser, default=None)
    flags.AddCacheKeyIncludeHost(parser, default=None)
    flags.AddCacheKeyIncludeQueryString(parser, default=None)
    flags.AddCacheKeyQueryStringList(parser)
    flags.AddSessionAffinity(parser, internal_lb=True)
    flags.AddAffinityCookieTtl(parser)
    AddIapFlag(parser)

  def Modify(self, args, existing):
    replacement = super(UpdateAlpha, self).Modify(args, existing)

    if args.connection_draining_timeout is not None:
      replacement.connectionDraining = self.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout)

    self._ApplyIapArgs(args.iap, existing, replacement)

    cache_key_policy = self.messages.CacheKeyPolicy()
    if (replacement.cdnPolicy is not None and
        replacement.cdnPolicy.cacheKeyPolicy is not None):
      cache_key_policy = replacement.cdnPolicy.cacheKeyPolicy
    backend_services_utils.ValidateCacheKeyPolicyArgs(args)
    backend_services_utils.UpdateCacheKeyPolicy(args, cache_key_policy)
    if (args.cache_key_include_protocol is not None or
        args.cache_key_include_host is not None or
        args.cache_key_include_query_string is not None or
        args.cache_key_query_string_whitelist is not None or
        args.cache_key_query_string_blacklist is not None):
      replacement.cdnPolicy = self.messages.BackendServiceCdnPolicy(
          cacheKeyPolicy=cache_key_policy)

    return replacement

  def ValidateArgs(self, args):
    if not any([
        args.affinity_cookie_ttl is not None,
        args.connection_draining_timeout is not None,
        args.description is not None,
        args.enable_cdn is not None,
        args.cache_key_include_protocol is not None,
        args.cache_key_include_host is not None,
        args.cache_key_include_query_string is not None,
        args.cache_key_query_string_whitelist is not None,
        args.cache_key_query_string_blacklist is not None,
        args.http_health_checks,
        args.iap is not None,
        args.port,
        args.port_name,
        args.protocol,
        args.session_affinity is not None,
        args.timeout is not None,
        getattr(args, 'health_checks', None),
        getattr(args, 'https_health_checks', None),
    ]):
      raise exceptions.ToolException('At least one property must be modified.')


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(UpdateGA):
  """Update a backend service."""

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    flags.AddDescription(parser)
    flags.AddHealthChecks(parser)
    flags.AddHttpHealthChecks(parser)
    flags.AddHttpsHealthChecks(parser)
    flags.AddTimeout(parser, default=None)
    flags.AddPortName(parser)
    flags.AddProtocol(parser, default=None)

    flags.AddConnectionDrainingTimeout(parser)
    flags.AddEnableCdn(parser, default=None)
    flags.AddSessionAffinity(parser, internal_lb=True)
    flags.AddAffinityCookieTtl(parser)
    AddIapFlag(parser)

  def Modify(self, args, existing):
    replacement = super(UpdateBeta, self).Modify(args, existing)

    if args.connection_draining_timeout is not None:
      replacement.connectionDraining = self.messages.ConnectionDraining(
          drainingTimeoutSec=args.connection_draining_timeout)

    self._ApplyIapArgs(args.iap, existing, replacement)

    return replacement

  def ValidateArgs(self, args):
    if not any([
        args.affinity_cookie_ttl is not None,
        args.connection_draining_timeout is not None,
        args.description is not None,
        args.enable_cdn is not None,
        args.health_checks,
        args.http_health_checks,
        args.https_health_checks,
        args.iap is not None,
        args.port,
        args.port_name,
        args.protocol,
        args.session_affinity is not None,
        args.timeout is not None,
    ]):
      raise exceptions.ToolException('At least one property must be modified.')


UpdateGA.detailed_help = {
    'brief': 'Update a backend service',
    'DESCRIPTION': """
        *{command}* is used to update backend services.
        """,
}
UpdateAlpha.detailed_help = UpdateGA.detailed_help
UpdateBeta.detailed_help = UpdateGA.detailed_help
