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
"""Command for creating target SSL proxies."""

from googlecloudsdk.api_lib.compute import base_classes


class Create(base_classes.BaseAsyncCreator):
  """Create a target SSL proxy."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--description',
        help='An optional, textual description for the target SSL proxy.')

    ssl_certificate = parser.add_argument(
        '--ssl-certificate',
        required=True,
        help=('A reference to an SSL certificate resource that is used for '
              'server-side authentication.'))
    ssl_certificate.detailed_help = """\
        A reference to an SSL certificate resource that is used for
        server-side authentication. The SSL certificate must exist and cannot
        be deleted while referenced by a target SSL proxy.
        """

    backend_service = parser.add_argument(
        '--backend-service',
        required=True,
        help=('.'))
    backend_service.detailed_help = """\
        A backend service that will be used for connections to the target SSL
        proxy.
        """

    proxy_header_options = ['NONE', 'PROXY_V1']

    proxy_header = parser.add_argument(
        '--proxy-header',
        choices=proxy_header_options,
        help=('.'))
    proxy_header.detailed_help = """\
        Format of the proxy header that the balancer will send when creating new
        backend connections.  Valid options are: NONE and PROXY_V1.
        """

    parser.add_argument(
        'name',
        help='The name of the target SSL proxy.')

  @property
  def service(self):
    return self.compute.targetSslProxies

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'targetSslProxies'

  def CreateRequests(self, args):
    ssl_certificate_ref = self.CreateGlobalReference(
        args.ssl_certificate, resource_type='sslCertificates')

    backend_service_ref = self.CreateGlobalReference(
        args.backend_service, resource_type='backendServices')

    target_ssl_proxy_ref = self.CreateGlobalReference(
        args.name, resource_type='targetSslProxies')

    if args.proxy_header:
      proxy_header = self.messages.TargetSslProxy.ProxyHeaderValueValuesEnum(
          args.proxy_header)
    else:
      proxy_header = (
          self.messages.TargetSslProxy.ProxyHeaderValueValuesEnum.NONE)

    request = self.messages.ComputeTargetSslProxiesInsertRequest(
        project=self.project,
        targetSslProxy=self.messages.TargetSslProxy(
            description=args.description,
            name=target_ssl_proxy_ref.Name(),
            proxyHeader=proxy_header,
            service=backend_service_ref.SelfLink(),
            sslCertificates=[ssl_certificate_ref.SelfLink()]))
    return [request]


Create.detailed_help = {
    'brief': 'Create a target SSL proxy',
    'DESCRIPTION': """
        *{command}* is used to create target SSL proxies. A target
        SSL proxy is referenced by one or more forwarding rules which
        define which packets the proxy is responsible for routing. The
        target SSL proxy points to a backend service which handle the
        actual requests. The target SSL proxy also points to an SSL
        certificate used for server-side authentication.
        """,
}
