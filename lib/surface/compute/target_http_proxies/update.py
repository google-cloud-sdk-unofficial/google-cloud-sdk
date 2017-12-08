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
"""Command for updating target HTTP proxies."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute.target_http_proxies import flags


class Update(base_classes.NoOutputAsyncMutator):
  """Update a target HTTP proxy."""

  TARGET_HTTP_PROXY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.TARGET_HTTP_PROXY_ARG = flags.TargetHttpProxyArgument()
    cls.TARGET_HTTP_PROXY_ARG.AddArgument(parser)

    parser.add_argument(
        '--url-map',
        required=True,
        help="""\
        A reference to a URL map resource that will define the mapping of
        URLs to backend services. The URL map must exist and cannot be
        deleted while referenced by a target HTTP proxy.
        """)

  @property
  def service(self):
    return self.compute.targetHttpProxies

  @property
  def method(self):
    return 'SetUrlMap'

  @property
  def resource_type(self):
    return 'targetHttpProxies'

  def CreateRequests(self, args):
    url_map_ref = self.CreateGlobalReference(
        args.url_map, resource_type='urlMaps')

    target_http_proxy_ref = self.TARGET_HTTP_PROXY_ARG.ResolveAsResource(
        args, self.resources)

    request = self.messages.ComputeTargetHttpProxiesSetUrlMapRequest(
        project=self.project,
        targetHttpProxy=target_http_proxy_ref.Name(),
        urlMapReference=self.messages.UrlMapReference(
            urlMap=url_map_ref.SelfLink()))

    return [request]


Update.detailed_help = {
    'brief': 'Update a target HTTP proxy',
    'DESCRIPTION': """\
        *{command}* is used to change the URL map of existing
        target HTTP proxies. A target HTTP proxy is referenced
        by one or more forwarding rules which
        define which packets the proxy is responsible for routing. The
        target HTTP proxy in turn points to a URL map that defines the rules
        for routing the requests. The URL map's job is to map URLs to
        backend services which handle the actual requests.
        """,
}
