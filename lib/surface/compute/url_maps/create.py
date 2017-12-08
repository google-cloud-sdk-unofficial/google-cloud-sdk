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


def _Args(parser):
  """Common arguments to create commands for each release track."""
  parser.add_argument(
      '--description',
      help='An optional, textual description for the URL map.')
  parser.add_argument(
      'name',
      help='The name of the URL map.')


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class CreateGA(base_classes.BaseAsyncCreator):
  """Create a URL map."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    parser.add_argument(
        '--default-service',
        required=True,
        help=('A backend service that will be used for requests for which this '
              'URL map has no mappings.'))

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
    default_service_uri = self.CreateGlobalReference(
        args.default_service, resource_type='backendServices').SelfLink()

    url_map_ref = self.CreateGlobalReference(args.name)

    request = self.messages.ComputeUrlMapsInsertRequest(
        project=self.project,
        urlMap=self.messages.UrlMap(
            defaultService=default_service_uri,
            description=args.description,
            name=url_map_ref.Name()))
    return [request]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateGA):
  """Create a URL map."""

  @staticmethod
  def Args(parser):
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
      default_backend_uri = self.CreateGlobalReference(
          args.default_service,
          resource_type='backendServices').SelfLink()
    else:
      default_backend_uri = self.CreateGlobalReference(
          args.default_backend_bucket,
          resource_type='backendBuckets').SelfLink()

    url_map_ref = self.CreateGlobalReference(args.name)

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
        after the map is created by using 'gcloud compute url-maps
        edit' or by using 'gcloud compute url-maps add-path-matcher'
        and 'gcloud compute url-maps add-host-rule'.
        """,
}
CreateAlpha.detailed_help = {
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
        after the map is created by using 'gcloud compute url-maps
        edit' or by using 'gcloud compute url-maps add-path-matcher'
        and 'gcloud compute url-maps add-host-rule'.
        """,
}
