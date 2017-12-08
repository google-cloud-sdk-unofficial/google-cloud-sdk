# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Command for cache invalidation."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import batch_helper
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import property_selector
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.core import log


class InvalidateCache(base_classes.BaseCommand):
  """Invalidate specified objects for a URL map in Cloud CDN caches."""

  @staticmethod
  def Args(parser):
    path = parser.add_argument(
        '--path',
        required=True,
        help=('Specifies the set of paths within the URL map to '
              'invalidate.'))

    parser.add_argument(
        '--async',
        action='store_true',
        help='Do not wait for the operation to complete.',)

    path.detailed_help = """\
        A path specifying which objects to invalidate. PATH must start with
        ``/'' and the only place a ``*'' is allowed is at the end following a
        ``/''. It will be matched against URL paths, which do not include
        scheme, host, or any text after the first ``?'' or ``#'' (and those
        characters are not allowed here). For example, for the URL
        ``https://example.com/whatever/x.html?a=b'', the path is
        ``/whatever/x.html''.

        If PATH ends with ``*'', the preceding string is a prefix, and all URLs
        whose paths begin with it will be invalidated. If PATH doesn't end with
        ``*'', then only URLs with exactly that path will be invalidated.

        Examples:
        - ``'', ``*'', anything that doesn't start with ``/'': error
        - ``/'': just the root URL
        - ``/*'': everything
        - ``/x/y'': ``/x/y'' only (and not ``/x/y/'')
        - ``/x/y/'': ``/x/y/'' only (and not ``/x/y'')
        - ``/x/y/*'': ``/x/y/'' and everything under it
        """

    parser.add_argument(
        'urlmap',
        completion_resource='compute.urlMaps',
        help='The name of the URL map.')

  @property
  def method(self):
    return 'InvalidateCache'

  @property
  def service(self):
    return self.compute.urlMaps

  def CreateRequests(self, args):
    """Returns a list of requests necessary for cache invalidations."""
    url_map_ref = self.CreateGlobalReference(
        args.urlmap, resource_type='urlMaps')
    request = self.messages.ComputeUrlMapsInvalidateCacheRequest(
        project=self.project,
        urlMap=url_map_ref.Name(),
        cacheInvalidationRule=self.messages.CacheInvalidationRule(
            path=args.path))

    return [request]

  def Run(self, args):
    request_protobufs = self.CreateRequests(args)
    requests = []
    for request in request_protobufs:
      requests.append((self.service, self.method, request))

    errors = []
    if args.async:
      resources, new_errors = batch_helper.MakeRequests(
          requests=requests,
          http=self.http,
          batch_url=self.batch_url)
      if not new_errors:
        for invalidation_operation in resources:
          log.status.write('Invalidation pending for [{0}]\n'.format(
              invalidation_operation.targetLink))
          log.status.write('Monitor its progress at [{0}]\n'.format(
              invalidation_operation.selfLink))
      errors.extend(new_errors)
    else:
      # We want to run through the generator that MakeRequests returns in order
      # to actually make the requests.
      resources = list(request_helper.MakeRequests(
          requests=requests,
          http=self.http,
          batch_url=self.batch_url,
          errors=errors,
          custom_get_requests=None))

    resources = lister.ProcessResults(
        resources=resources,
        field_selector=property_selector.PropertySelector(
            properties=None,
            transformations=self.transformations))

    if errors:
      utils.RaiseToolException(errors)

    return resources

  def Format(self, args):
    return 'none'


InvalidateCache.detailed_help = {
    'brief': 'Invalidate specified objects for a URL map in Cloud CDN caches',
    'DESCRIPTION': """
        *{command}* requests that Cloud CDN stop using cached content for
        resources at a particular URL path or set of URL paths.

        *{command}* may succeed even if no content is cached for some or all
        URLs with the given path.
        """,
}
