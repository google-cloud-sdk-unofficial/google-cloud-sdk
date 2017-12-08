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
"""Command for updating target HTTPS proxies."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.ssl_certificates import (
    flags as ssl_certificate_flags)
from googlecloudsdk.command_lib.compute.target_https_proxies import flags
from googlecloudsdk.command_lib.compute.url_maps import flags as url_map_flags


class Update(base_classes.NoOutputAsyncMutator):
  """Update a target HTTPS proxy."""

  SSL_CERTIFICATE_ARG = None
  TARGET_HTTPS_PROXY_ARG = None
  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SSL_CERTIFICATE_ARG = (
        ssl_certificate_flags.SslCertificateArgumentForOtherResource(
            'target HTTPS proxy', required=False))
    cls.SSL_CERTIFICATE_ARG.AddArgument(parser)
    cls.TARGET_HTTPS_PROXY_ARG = flags.TargetHttpsProxyArgument()
    cls.TARGET_HTTPS_PROXY_ARG.AddArgument(parser)
    cls.URL_MAP_ARG = url_map_flags.UrlMapArgumentForTargetHttpsProxy(
        required=False)
    cls.URL_MAP_ARG.AddArgument(parser)

  @property
  def service(self):
    return self.compute.targetHttpsProxies

  @property
  def method(self):
    pass

  @property
  def resource_type(self):
    return 'targetHttpProxies'

  def CreateRequests(self, args):

    if not args.ssl_certificate and not args.url_map:
      raise exceptions.ToolException(
          'You must specify at least one of [--ssl-certificate] or '
          '[--url-map].')

    requests = []
    target_https_proxy_ref = self.TARGET_HTTPS_PROXY_ARG.ResolveAsResource(
        args, self.resources)

    if args.ssl_certificate:
      ssl_certificate_ref = self.SSL_CERTIFICATE_ARG.ResolveAsResource(
          args, self.resources)
      requests.append(
          ('SetSslCertificates',
           self.messages.ComputeTargetHttpsProxiesSetSslCertificatesRequest(
               project=self.project,
               targetHttpsProxy=target_https_proxy_ref.Name(),
               targetHttpsProxiesSetSslCertificatesRequest=(
                   self.messages.TargetHttpsProxiesSetSslCertificatesRequest(
                       sslCertificates=[ssl_certificate_ref.SelfLink()])))))

    if args.url_map:
      url_map_ref = self.URL_MAP_ARG.ResolveAsResource(args, self.resources)
      requests.append(('SetUrlMap',
                       self.messages.ComputeTargetHttpsProxiesSetUrlMapRequest(
                           project=self.project,
                           targetHttpsProxy=target_https_proxy_ref.Name(),
                           urlMapReference=self.messages.UrlMapReference(
                               urlMap=url_map_ref.SelfLink()))))

    return requests


Update.detailed_help = {
    'brief':
        'Update a target HTTPS proxy',
    'DESCRIPTION':
        """\
        *{command}* is used to change the SSL certificate and/or URL map of
        existing target HTTPS proxies. A target HTTPS proxy is referenced
        by one or more forwarding rules which
        define which packets the proxy is responsible for routing. The
        target HTTPS proxy in turn points to a URL map that defines the rules
        for routing the requests. The URL map's job is to map URLs to
        backend services which handle the actual requests. The target
        HTTPS proxy also points to an SSL certificate used for
        server-side authentication.
        """,
}
