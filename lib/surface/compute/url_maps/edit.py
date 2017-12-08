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
"""Command for modifying URL maps."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources


class InvalidResourceError(exceptions.ToolException):
  # Normally we'd want to subclass core.exceptions.Error, but base_classes.Edit
  # abuses ToolException to classify errors when displaying messages to users,
  # and we should continue to fit in that framework for now.
  pass


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class EditGA(base_classes.BaseEdit):
  """Modify URL maps."""

  @staticmethod
  def Args(parser):
    base_classes.BaseEdit.Args(parser)
    parser.add_argument(
        'name',
        help='The name of the URL map to modify.')

  @property
  def service(self):
    return self.compute.urlMaps

  @property
  def resource_type(self):
    return 'urlMaps'

  @property
  def example_resource(self):
    uri_prefix = ('https://www.googleapis.com/compute/v1/projects/'
                  'my-project/global/backendServices/')
    return self.messages.UrlMap(
        name='site-map',
        defaultService=uri_prefix + 'default-service',
        hostRules=[
            self.messages.HostRule(
                hosts=['*.google.com', 'google.com'],
                pathMatcher='www'),
            self.messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='www',
                defaultService=uri_prefix + 'www-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=uri_prefix + 'search'),
                    self.messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=uri_prefix + 'ads'),
                    self.messages.PathRule(
                        paths=['/images'],
                        service=uri_prefix + 'images'),
                ]),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=uri_prefix + 'youtube-default',
                pathRules=[
                    self.messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=uri_prefix + 'youtube-search'),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=uri_prefix + 'youtube-watch'),
                ]),
        ],
        tests=[
            self.messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=uri_prefix + 'ads'),
            self.messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=uri_prefix + 'youtube-default'),
        ],
    )

  def CreateReference(self, args):
    return self.CreateGlobalReference(args.name)

  @property
  def reference_normalizers(self):
    def NormalizeBackendService(value):
      return self.CreateGlobalReference(
          value, resource_type='backendServices').SelfLink()

    return [
        ('defaultService', NormalizeBackendService),
        ('pathMatchers[].defaultService', NormalizeBackendService),
        ('pathMatchers[].pathRules[].service', NormalizeBackendService),
        ('tests[].service', NormalizeBackendService),
    ]

  def GetGetRequest(self, args):
    return (
        self.service,
        'Get',
        self.messages.ComputeUrlMapsGetRequest(
            project=self.project,
            urlMap=args.name))

  def GetSetRequest(self, args, replacement, _):
    return (
        self.service,
        'Update',
        self.messages.ComputeUrlMapsUpdateRequest(
            project=self.project,
            urlMap=args.name,
            urlMapResource=replacement))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EditAlpha(EditGA):
  """Modify URL maps."""

  @property
  def example_resource(self):
    backend_service_uri_prefix = (
        'https://www.googleapis.com/compute/alpha/projects/'
        'my-project/global/backendServices/')
    backend_bucket_uri_prefix = (
        'https://www.googleapis.com/compute/alpha/projects/'
        'my-project/global/backendBuckets/')
    return self.messages.UrlMap(
        name='site-map',
        defaultService=backend_service_uri_prefix + 'default-service',
        hostRules=[
            self.messages.HostRule(hosts=['*.google.com', 'google.com'],
                                   pathMatcher='www'),
            self.messages.HostRule(hosts=['*.youtube.com', 'youtube.com',
                                          '*-youtube.com'],
                                   pathMatcher='youtube'),
        ],
        pathMatchers=[
            self.messages.PathMatcher(
                name='www',
                defaultService=backend_service_uri_prefix + 'www-default',
                pathRules=[
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=backend_service_uri_prefix +
                                           'search'),
                    self.messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=backend_service_uri_prefix + 'ads'),
                    self.messages.PathRule(paths=['/images/*'],
                                           service=backend_bucket_uri_prefix +
                                           'images'),
                ]),
            self.messages.PathMatcher(
                name='youtube',
                defaultService=backend_service_uri_prefix + 'youtube-default',
                pathRules=[
                    self.messages.PathRule(paths=['/search', '/search/*'],
                                           service=backend_service_uri_prefix +
                                           'youtube-search'),
                    self.messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=backend_service_uri_prefix + 'youtube-watch'),
                ]),
        ],
        tests=[
            self.messages.UrlMapTest(host='www.google.com',
                                     path='/search/ads/inline?q=flowers',
                                     service=backend_service_uri_prefix +
                                     'ads'),
            self.messages.UrlMapTest(host='youtube.com',
                                     path='/watch/this',
                                     service=backend_service_uri_prefix +
                                     'youtube-default'),
            self.messages.UrlMapTest(host='youtube.com',
                                     path='/images/logo.png',
                                     service=backend_bucket_uri_prefix +
                                     'images'),
        ],)

  @property
  def reference_normalizers(self):

    def MakeReferenceNormalizer(field_name, allowed_collections):
      """Returns a function to normalize resource references."""
      def NormalizeReference(reference):
        """Returns normalized URI for field_name."""
        try:
          value_ref = self.resources.Parse(reference)
        except resources.UnknownCollectionException:
          raise InvalidResourceError(
              '[{field_name}] must be referenced using URIs.'.format(
                  field_name=field_name))

        if value_ref.Collection() not in allowed_collections:
          raise InvalidResourceError(
              'Invalid [{field_name}] reference: [{value}].'. format(
                  field_name=field_name, value=reference))
        return value_ref.SelfLink()
      return NormalizeReference

    allowed_collections = ['compute.backendServices', 'compute.backendBuckets']
    return [
        ('defaultService', MakeReferenceNormalizer(
            'defaultService', allowed_collections)),
        ('pathMatchers[].defaultService', MakeReferenceNormalizer(
            'defaultService', allowed_collections)),
        ('pathMatchers[].pathRules[].service', MakeReferenceNormalizer(
            'service', allowed_collections)),
        ('tests[].service', MakeReferenceNormalizer(
            'service', allowed_collections)),
    ]


EditGA.detailed_help = {
    'brief': 'Modify URL maps',
    'DESCRIPTION': """\
        *{command}* can be used to modify a URL map. The URL map
        resource is fetched from the server and presented in a text
        editor. After the file is saved and closed, this command will
        update the resource. Only fields that can be modified are
        displayed in the editor.

        The editor used to modify the resource is chosen by inspecting
        the ``EDITOR'' environment variable.
        """,
}
EditAlpha.detailed_help = EditGA.detailed_help
