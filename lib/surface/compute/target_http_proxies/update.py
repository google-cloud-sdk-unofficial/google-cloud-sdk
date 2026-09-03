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
"""Command for updating target HTTP proxies."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import target_proxies_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_http_proxies import flags
from googlecloudsdk.command_lib.compute.target_http_proxies import target_http_proxies_utils
from googlecloudsdk.command_lib.compute.url_maps import flags as url_map_flags
from googlecloudsdk.command_lib.network_services import flags as network_services_flags


def _DetailedHelp():
  return {
      'brief': 'Update a target HTTP proxy.',
      'DESCRIPTION': """\
      *{command}* is used to change the URL map of existing target
      HTTP proxies. A target HTTP proxy is referenced by one or more
      forwarding rules which specify the network traffic that the proxy
      is responsible for routing. The target HTTP proxy points to a URL
      map that defines the rules for routing the requests. The URL map's
      job is to map URLs to backend services which handle the actual
      requests.
      """,
      'EXAMPLES': """\
      If there is an already-created URL map with the name URL_MAP, update a
      global target HTTP proxy pointing to this map by running:

        $ {command} PROXY_NAME --url-map=URL_MAP

      Update a regional target HTTP proxy by running:

        $ {command} PROXY_NAME --url-map=URL_MAP --region=REGION_NAME
      """,
  }


def _CheckMissingArgument(args, support_http_filters=False):
  """Validates that at least one property to update is specified."""
  all_args = [
      'url_map',
      'http_keep_alive_timeout_sec',
      'clear_http_keep_alive_timeout_sec',
  ]
  err_msg_args = [
      '[--url-map]',
      '[--http-keep-alive-timeout-sec]',
      '[--clear-http-keep-alive-timeout-sec]',
  ]
  if support_http_filters:
    all_args.extend(['http_filters', 'clear_http_filters'])
    err_msg_args.extend(['[--http-filters]', '[--clear-http-filters]'])
  if not any(args.IsSpecified(arg) for arg in all_args):
    raise exceptions.MinimumArgumentException(
        err_msg_args, 'Please specify at least one property to update.'
    )


def _Run(
    args,
    holder,
    target_http_proxy_arg,
    url_map_arg,
    http_filters=None,
    clear_http_filters=False,
):
  """Issues requests necessary to update Target HTTP Proxies."""
  client = holder.client

  proxy_ref = target_http_proxy_arg.ResolveAsResource(
      args,
      holder.resources,
      default_scope=compute_scope.ScopeEnum.GLOBAL,
      scope_lister=compute_flags.GetDefaultScopeLister(client),
  )

  url_map_ref = target_http_proxies_utils.ResolveTargetHttpProxyUrlMap(
      args, url_map_arg, proxy_ref, holder.resources
  )

  if target_http_proxies_utils.IsRegionalTargetHttpProxiesRef(proxy_ref):
    invalid_arg = None
    if args.IsSpecified('http_keep_alive_timeout_sec'):
      invalid_arg = '--http-keep-alive-timeout-sec'
    elif args.IsSpecified('clear_http_keep_alive_timeout_sec'):
      invalid_arg = '--clear-http-keep-alive-timeout-sec'
    elif http_filters is not None:
      invalid_arg = '--http-filters'
    elif clear_http_filters:
      invalid_arg = '--clear-http-filters'
    if invalid_arg is not None:
      if invalid_arg in ('--http-filters', '--clear-http-filters'):
        raise exceptions.InvalidArgumentException(
            invalid_arg,
            'http filters are not patchable for regional target HTTP proxies',
        )
      raise exceptions.InvalidArgumentException(
          invalid_arg,
          'http keep alive timeout is not patchable for regional target HTTP'
          ' proxies',
      )

    if not url_map_ref:
      raise exceptions.InvalidArgumentException(
          '--url-map',
          'URL map must be specified for regional target HTTP proxies',
      )

    request = client.messages.ComputeRegionTargetHttpProxiesSetUrlMapRequest(
        project=proxy_ref.project,
        region=proxy_ref.region,
        targetHttpProxy=proxy_ref.Name(),
        urlMapReference=client.messages.UrlMapReference(
            urlMap=url_map_ref.SelfLink()
        ),
    )
    collection = client.apitools_client.regionTargetHttpProxies
    res = client.MakeRequests([(collection, 'SetUrlMap', request)])
    return res
  else:
    old_resource = _GetGlobalTargetHttpProxy(client, proxy_ref)
    new_resource = encoding.CopyProtoMessage(old_resource)
    cleared_fields = []

    if args.url_map:
      new_resource.urlMap = url_map_ref.SelfLink()

    if args.IsSpecified('http_keep_alive_timeout_sec'):
      new_resource.httpKeepAliveTimeoutSec = args.http_keep_alive_timeout_sec
    elif args.IsSpecified('clear_http_keep_alive_timeout_sec'):
      new_resource.httpKeepAliveTimeoutSec = None
      cleared_fields.append('httpKeepAliveTimeoutSec')

    if http_filters:
      new_resource.httpFilters = [ref.SelfLink() for ref in http_filters]
    elif clear_http_filters:
      new_resource.httpFilters = []
      cleared_fields.append('httpFilters')

    if old_resource != new_resource:
      return _PatchGlobalTargetHttpProxy(
          client, proxy_ref, new_resource, cleared_fields
      )


def _GetGlobalTargetHttpProxy(client, proxy_ref):
  """Retrieves the Global target HTTP proxy."""

  requests = []
  requests.append((
      client.apitools_client.targetHttpProxies,
      'Get',
      client.messages.ComputeTargetHttpProxiesGetRequest(
          project=proxy_ref.project, targetHttpProxy=proxy_ref.Name()
      ),
  ))

  res = client.MakeRequests(requests)
  return res[0]


def _PatchGlobalTargetHttpProxy(
    client, proxy_ref, new_resource, cleared_fields
):
  """Patches the Global target HTTP proxy."""
  requests = []
  requests.append((
      client.apitools_client.targetHttpProxies,
      'Patch',
      client.messages.ComputeTargetHttpProxiesPatchRequest(
          project=proxy_ref.project,
          targetHttpProxy=proxy_ref.Name(),
          targetHttpProxyResource=new_resource,
      ),
  ))
  with client.apitools_client.IncludeFields(cleared_fields):
    return client.MakeRequests(requests)


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA,
    base.ReleaseTrack.PREVIEW,
)
class Update(base.UpdateCommand):
  """Update a target HTTP proxy."""

  _support_http_filters = False
  _url_map_required = True

  TARGET_HTTP_PROXY_ARG = None
  URL_MAP_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.TARGET_HTTP_PROXY_ARG = flags.TargetHttpProxyArgument()
    cls.TARGET_HTTP_PROXY_ARG.AddArgument(parser, operation_type='update')
    cls.URL_MAP_ARG = url_map_flags.UrlMapArgumentForTargetProxy(
        required=cls._url_map_required
    )
    cls.URL_MAP_ARG.AddArgument(parser)

    group = parser.add_mutually_exclusive_group()
    target_proxies_utils.AddHttpKeepAliveTimeoutSec(group)
    target_proxies_utils.AddClearHttpKeepAliveTimeoutSec(group)

    if cls._support_http_filters:
      http_filters_group = parser.add_mutually_exclusive_group()
      network_services_flags.GetHttpFilterResourceArg(
          'to attach',
          name='http-filters',
          required=False,
          plural=True,
          group=http_filters_group,
      ).AddToParser(http_filters_group)
      http_filters_group.add_argument(
          '--clear-http-filters',
          action='store_true',
          default=None,
          help='Clear existing HTTP filters.',
      )

  def Run(self, args):
    _CheckMissingArgument(
        args, support_http_filters=self._support_http_filters
    )
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    http_filters = None
    clear_http_filters = False
    if self._support_http_filters:
      if args.IsKnownAndSpecified('http_filters'):
        http_filters = args.CONCEPTS.http_filters.Parse()
      clear_http_filters = args.IsKnownAndSpecified('clear_http_filters')
    return _Run(
        args,
        holder,
        self.TARGET_HTTP_PROXY_ARG,
        self.URL_MAP_ARG,
        http_filters=http_filters,
        clear_http_filters=clear_http_filters,
    )


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update a target HTTP proxy."""

  _support_http_filters = True
  _url_map_required = False

