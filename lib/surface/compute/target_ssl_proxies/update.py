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
"""Command for updating target SSL proxies."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import exceptions


class Update(base_classes.NoOutputAsyncMutator):
  """Update a target SSL proxy."""

  @staticmethod
  def Args(parser):

    # TODO(user) This probably shouldn't be a mutualy exclusive
    # group the service falls over when two update requests come in
    # as part of the same batch request.  See b/18760514.
    group = parser.add_mutually_exclusive_group()

    ssl_certificate = group.add_argument(
        '--ssl-certificate',
        help=('A reference to an SSL certificate resource that is used for '
              'server-side authentication.'))
    ssl_certificate.detailed_help = """\
        A reference to an SSL certificate resource that is used for
        server-side authentication. The SSL certificate must exist and cannot
        be deleted while referenced by a target SSL proxy.
        """

    backend_service = parser.add_argument(
        '--backend-service',
        help=('A backend service that will be used for connections to the '
              'target SSLproxy.'))
    backend_service.detailed_help = """\
        A backend service that will be used for connections to the target SSL
        proxy.
        """

    proxy_header_options = ['NONE', 'PROXY_V1']

    proxy_header = parser.add_argument(
        '--proxy-header',
        choices=proxy_header_options,
        help=('Proxy header format.'))
    proxy_header.detailed_help = """\
        Format of the proxy header that the balancer will send when creating new
        backend connections.  Valid options are: NONE and PROXY_V1.
        """

    parser.add_argument(
        'name',
        completion_resource='TargetSslProxies',
        help='The name of the target SSL proxy.')

  @property
  def service(self):
    return self.compute.targetSslProxies

  @property
  def method(self):
    pass

  @property
  def resource_type(self):
    return 'targetHttpProxies'

  def CreateRequests(self, args):

    if not (args.ssl_certificate or args.proxy_header or args.backend_service):
      raise exceptions.ToolException(
          'You must specify at least one of [--ssl-certificate], '
          '[--backend-service] or [--proxy-header].')

    requests = []
    target_ssl_proxy_ref = self.CreateGlobalReference(
        args.name, resource_type='targetSslProxies')

    if args.ssl_certificate:
      ssl_certificate_ref = self.CreateGlobalReference(
          args.ssl_certificate, resource_type='sslCertificates')
      requests.append(
          ('SetSslCertificates',
           self.messages.ComputeTargetSslProxiesSetSslCertificatesRequest(
               project=self.project,
               targetSslProxy=target_ssl_proxy_ref.Name(),
               targetSslProxiesSetSslCertificatesRequest=(
                   self.messages.TargetSslProxiesSetSslCertificatesRequest(
                       sslCertificates=[ssl_certificate_ref.SelfLink()])))))

    if args.backend_service:
      backend_service_ref = self.CreateGlobalReference(
          args.backend_service, resource_type='backendServices')
      requests.append(
          ('SetBackendService',
           self.messages.ComputeTargetSslProxiesSetBackendServiceRequest(
               project=self.project,
               targetSslProxy=target_ssl_proxy_ref.Name(),
               targetSslProxiesSetBackendServiceRequest=(
                   self.messages.TargetSslProxiesSetBackendServiceRequest(
                       service=backend_service_ref.SelfLink())))))

    if args.proxy_header:
      proxy_header = (self.messages.TargetSslProxiesSetProxyHeaderRequest.
                      ProxyHeaderValueValuesEnum(args.proxy_header))
      requests.append(
          ('SetProxyHeader',
           self.messages.ComputeTargetSslProxiesSetProxyHeaderRequest(
               project=self.project,
               targetSslProxy=target_ssl_proxy_ref.Name(),
               targetSslProxiesSetProxyHeaderRequest=(
                   self.messages.TargetSslProxiesSetProxyHeaderRequest(
                       proxyHeader=proxy_header)))))

    return requests


Update.detailed_help = {
    'brief': 'Update a target SSL proxy',
    'DESCRIPTION': """\

        *{command}* is used to change the SSL certificate, backend
        service or proxy header of existing target SSL proxies. A
        target SSL proxy is referenced by one or more forwarding rules
        which define which packets the proxy is responsible for
        routing. The target SSL proxy in turn points to a backend
        service which will handle the requests. The target SSL proxy
        also points to an SSL certificate used for server-side
        authentication.  """,
}
