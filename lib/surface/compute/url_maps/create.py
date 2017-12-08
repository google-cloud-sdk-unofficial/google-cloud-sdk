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
"""Command for creating URL maps."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.backend_buckets import (
    flags as backend_bucket_flags)
from googlecloudsdk.command_lib.compute.backend_services import (
    flags as backend_service_flags)
from googlecloudsdk.command_lib.compute.url_maps import flags


def _Args(parser):
  """Common arguments to create commands for each release track."""
  parser.add_argument(
      '--description',
      help='An optional, textual description for the URL map.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base_classes.BaseAsyncCreator):
  """Create a URL map."""

  BACKEND_SERVICE_ARG = None
  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForUrlMap())
    cls.BACKEND_SERVICE_ARG.AddArgument(parser)
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser)

    _Args(parser)

  @property
  def service(self):
    return self.compute.urlMaps

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'urlMaps'

  def CreateRequests(self, args):
    default_service_uri = self.BACKEND_SERVICE_ARG.ResolveAsResource(
        args, self.resources).SelfLink()

    url_map_ref = self.URL_MAP_ARG.ResolveAsResource(args, self.resources)

    request = self.messages.ComputeUrlMapsInsertRequest(
        project=self.project,
        urlMap=self.messages.UrlMap(
            defaultService=default_service_uri,
            description=args.description,
            name=url_map_ref.Name()))
    return [request]


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateBeta(CreateGA):
  """Create a URL map."""

  BACKEND_BUCKET_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.BACKEND_BUCKET_ARG = (
        backend_bucket_flags.BackendBucketArgumentForUrlMap(required=False))
    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForUrlMap(required=False))
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser)

    _Args(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--default-service',
        help=('A backend service that will be used for requests for which this '
              'URL map has no mappings. Exactly one of --default-service or '
              '--default-backend-bucket is required.'))
    group.add_argument(
        '--default-backend-bucket',
        help=('A backend bucket that will be used for requests for which this '
              'URL map has no mappings. Exactly one of --default-service or '
              '--default-backend-bucket is required.'))

  def CreateRequests(self, args):
    if args.default_service:
      default_backend_uri = self.BACKEND_SERVICE_ARG.ResolveAsResource(
          args, self.resources).SelfLink()
    else:
      default_backend_uri = self.BACKEND_BUCKET_ARG.ResolveAsResource(
          args, self.resources).SelfLink()

    url_map_ref = self.URL_MAP_ARG.ResolveAsResource(args, self.resources)

    request = self.messages.ComputeUrlMapsInsertRequest(
        project=self.project,
        urlMap=self.messages.UrlMap(defaultService=default_backend_uri,
                                    description=args.description,
                                    name=url_map_ref.Name()))
    return [request]


CreateGA.detailed_help = {
    'brief': 'Create a URL map',
    'DESCRIPTION': """
        *{command}* is used to create URL maps which map HTTP and
        HTTPS request URLs to backend services. Mappings are done
        using a longest-match strategy.

        There are two components to a mapping: a host rule and a path
        matcher. A host rule maps one or more hosts to a path
        matcher. A path matcher maps request paths to backend
        services. For example, a host rule can map the hosts
        ``*.google.com'' and ``google.com'' to a path matcher called
        ``www''. The ``www'' path matcher in turn can map the path
        ``/search/*'' to the search backend service and everything
        else to a default backend service.

        Host rules and patch matchers can be added to the URL map
        after the map is created by using `gcloud compute url-maps edit`
        or by using `gcloud compute url-maps add-path-matcher`
        and `gcloud compute url-maps add-host-rule`.
        """,
}
CreateBeta.detailed_help = {
    'brief': 'Create a URL map',
    'DESCRIPTION': """
        *{command}* is used to create URL maps which map HTTP and
        HTTPS request URLs to backend services and backend buckets.
        Mappings are done using a longest-match strategy.

        There are two components to a mapping: a host rule and a path
        matcher. A host rule maps one or more hosts to a path
        matcher. A path matcher maps request paths to backend
        services or backend buckets. For example, a host rule can map
        the hosts ``*.google.com'' and ``google.com'' to a path
        matcher called ``www''. The ``www'' path matcher in turn can
        map the path ``/search/*'' to the search backend service, the
        path ``/static/*'' to the static backend bucket  and everything
        else to a default backend service or default backend bucket.

        Host rules and patch matchers can be added to the URL map
        after the map is created by using `gcloud compute url-maps edit`
        or by using `gcloud compute url-maps add-path-matcher`
        and `gcloud compute url-maps add-host-rule`.
        """,
}
