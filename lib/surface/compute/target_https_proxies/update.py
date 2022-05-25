# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for updating target HTTPS proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import resource_args
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_certificates import (
    flags as ssl_certificates_flags)
from googlecloudsdk.command_lib.compute.ssl_policies import (flags as
                                                             ssl_policies_flags)
from googlecloudsdk.command_lib.compute.target_https_proxies import flags
from googlecloudsdk.command_lib.compute.target_https_proxies import target_https_proxies_utils
from googlecloudsdk.command_lib.compute.url_maps import flags as url_map_flags


def _DetailedHelp():
  return {
      'brief':
          'Update a target HTTPS proxy.',
      'DESCRIPTION':
          """
      *{command}* is used to change the SSL certificate and/or URL map of
      existing target HTTPS proxies. A target HTTPS proxy is referenced by
      one or more forwarding rules which specify the network traffic that
      the proxy is responsible for routing. The target HTTPS proxy in turn
      points to a URL map that defines the rules for routing the requests.
      The URL map's job is to map URLs to backend services which handle
      the actual requests. The target HTTPS proxy also points to at most
      15 SSL certificates used for server-side authentication. The target
      HTTPS proxy can be associated with at most one SSL policy.
      """,
      'EXAMPLES':
          """
      Update the URL map of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --url-map=URL_MAP

      Update the SSL certificate of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --ssl-certificates=SSL_CERTIFIFCATE

      Update the URL map of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --url-map=URL_MAP --region=REGION_NAME

      Update the SSL certificate of a global target HTTPS proxy by running:

        $ {command} PROXY_NAME --ssl-certificates=SSL_CERTIFIFCATE --region=REGION_NAME
      """,
  }


def _CheckMissingArgument(args, certificate_map):
  """Checks for missing argument."""
  all_args = [
      'ssl_certificates', 'url_map', 'quic_override', 'ssl_policy',
      'clear_ssl_policy'
  ]
  err_msg_args = [
      '[--ssl-certificates]', '[--url-map]', '[--quic-override]',
      '[--ssl-policy]', '[--clear-ssl-policy]'
  ]
  if certificate_map:
    all_args.append('certificate_map')
    err_msg_args.append('[--certificate-map]')
    all_args.append('clear_certificate_map')
    err_msg_args.append('[--clear-certificate-map]')
  if not sum(args.IsSpecified(arg) for arg in all_args):
    raise compute_exceptions.ArgumentError(
        'You must specify at least one of %s or %s.' %
        (', '.join(err_msg_args[:-1]), err_msg_args[-1]))


def _Run(args, holder, ssl_certificates_arg, target_https_proxy_arg,
         url_map_arg, ssl_policy_arg, certificate_map_ref):
  """Issues requests necessary to update Target HTTPS Proxies."""
  client = holder.client

  target_https_proxy_ref = target_https_proxy_arg.ResolveAsResource(
      args,
      holder.resources,
      default_scope=compute_scope.ScopeEnum.GLOBAL,
      scope_lister=compute_flags.GetDefaultScopeLister(client))

  old_resource = _GetTargetHttpsProxy(client, target_https_proxy_ref)
  new_resource = encoding.CopyProtoMessage(old_resource)
  cleared_fields = []

  if args.ssl_certificates:
    ssl_cert_refs = target_https_proxies_utils.ResolveSslCertificates(
        args, ssl_certificates_arg, target_https_proxy_ref, holder.resources)
    new_resource.sslCertificates = [ref.SelfLink() for ref in ssl_cert_refs]

  if args.url_map:
    new_resource.urlMap = target_https_proxies_utils.ResolveTargetHttpsProxyUrlMap(
        args, url_map_arg, target_https_proxy_ref, holder.resources).SelfLink()

  if args.quic_override:
    new_resource.quicOverride = client.messages.TargetHttpsProxy.QuicOverrideValueValuesEnum(
        args.quic_override)

  if args.ssl_policy:
    ssl_policy_ref = target_https_proxies_utils.ResolveSslPolicy(
        args, ssl_policy_arg, target_https_proxy_ref, holder.resources)
    new_resource.sslPolicy = ssl_policy_ref.SelfLink()

  if args.IsSpecified('clear_ssl_policy'):
    new_resource.sslPolicy = None
    cleared_fields.append('sslPolicy')

  if certificate_map_ref:
    new_resource.certificateMap = certificate_map_ref.SelfLink()

  if args.IsKnownAndSpecified('clear_certificate_map'):
    new_resource.certificateMap = None
    cleared_fields.append('certificateMap')

  if old_resource != new_resource:
    return _PatchTargetHttpsProxy(client, target_https_proxy_ref, new_resource,
                                  cleared_fields)
  return []


def _GetTargetHttpsProxy(client, target_https_proxy_ref):
  """Retrieves the target HTTPS proxy."""
  if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(
      target_https_proxy_ref):
    request = client.messages.ComputeRegionTargetHttpsProxiesGetRequest(
        **target_https_proxy_ref.AsDict())
    collection = client.apitools_client.regionTargetHttpsProxies
  else:
    request = client.messages.ComputeTargetHttpsProxiesGetRequest(
        **target_https_proxy_ref.AsDict())
    collection = client.apitools_client.targetHttpsProxies
  return client.MakeRequests([(collection, 'Get', request)])[0]


def _PatchTargetHttpsProxy(client, target_https_proxy_ref, new_resource,
                           cleared_fields):
  """Patches the target HTTPS proxy."""
  requests = []
  if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(
      target_https_proxy_ref):
    requests.append(
        (client.apitools_client.regionTargetHttpsProxies, 'Patch',
         client.messages.ComputeRegionTargetHttpsProxiesPatchRequest(
             project=target_https_proxy_ref.project,
             region=target_https_proxy_ref.region,
             targetHttpsProxy=target_https_proxy_ref.Name(),
             targetHttpsProxyResource=new_resource)))
  else:
    requests.append((client.apitools_client.targetHttpsProxies, 'Patch',
                     client.messages.ComputeTargetHttpsProxiesPatchRequest(
                         project=target_https_proxy_ref.project,
                         targetHttpsProxy=target_https_proxy_ref.Name(),
                         targetHttpsProxyResource=new_resource)))
  with client.apitools_client.IncludeFields(cleared_fields):
    return client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.SilentCommand):
  """Update a target HTTPS proxy."""

  # TODO(b/144022508): Remove _include_l7_internal_load_balancing
  _include_l7_internal_load_balancing = True
  _certificate_map = False
  _regional_ssl_policies = False

  SSL_CERTIFICATES_ARG = None
  TARGET_HTTPS_PROXY_ARG = None
  URL_MAP_ARG = None
  SSL_POLICY_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.SSL_CERTIFICATES_ARG = (
        ssl_certificates_flags.SslCertificatesArgumentForOtherResource(
            'target HTTPS proxy',
            required=False,
            include_l7_internal_load_balancing=cls
            ._include_l7_internal_load_balancing))
    if not cls._certificate_map:
      cls.SSL_CERTIFICATES_ARG.AddArgument(
          parser, cust_metavar='SSL_CERTIFICATE')

    cls.TARGET_HTTPS_PROXY_ARG = flags.TargetHttpsProxyArgument(
        include_l7_internal_load_balancing=cls
        ._include_l7_internal_load_balancing)
    cls.TARGET_HTTPS_PROXY_ARG.AddArgument(parser, operation_type='update')

    cls.URL_MAP_ARG = url_map_flags.UrlMapArgumentForTargetProxy(
        required=False,
        proxy_type='HTTPS',
        include_l7_internal_load_balancing=cls
        ._include_l7_internal_load_balancing)
    cls.URL_MAP_ARG.AddArgument(parser)

    if cls._certificate_map:
      group = parser.add_mutually_exclusive_group()
      cert_group = group.add_argument_group()
      cls.SSL_CERTIFICATES_ARG.AddArgument(
          cert_group, cust_metavar='SSL_CERTIFICATE')
      map_group = group.add_mutually_exclusive_group()
      resource_args.AddCertificateMapResourceArg(
          map_group,
          'to attach',
          name='certificate-map',
          positional=False,
          required=False,
          with_location=False)
      resource_args.GetClearCertificateMapArgumentForOtherResource(
          'HTTPS proxy').AddToParser(map_group)

    if cls._regional_ssl_policies:
      cls.SSL_POLICY_ARG = ssl_policies_flags.GetSslPolicyMultiScopeArgumentForOtherResource(
          'HTTPS', required=False)
    else:
      cls.SSL_POLICY_ARG = ssl_policies_flags.GetSslPolicyArgumentForOtherResource(
          'HTTPS', required=False)

    group = parser.add_mutually_exclusive_group()
    ssl_policy_group = group.add_argument_group()
    cls.SSL_POLICY_ARG.AddArgument(ssl_policy_group)

    ssl_policies_flags.GetClearSslPolicyArgumentForOtherResource(
        'HTTPS', required=False).AddToParser(group)

    target_proxies_utils.AddQuicOverrideUpdateArgs(parser)

  def Run(self, args):
    _CheckMissingArgument(args, self._certificate_map)
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    certificate_map_ref = args.CONCEPTS.certificate_map.Parse(
    ) if self._certificate_map else None
    return _Run(args, holder, self.SSL_CERTIFICATES_ARG,
                self.TARGET_HTTPS_PROXY_ARG, self.URL_MAP_ARG,
                self.SSL_POLICY_ARG, certificate_map_ref)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class UpdateAlphaBeta(Update):
  _certificate_map = True
  _regional_ssl_policies = True
