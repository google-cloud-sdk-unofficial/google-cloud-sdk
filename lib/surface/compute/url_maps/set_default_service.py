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
"""Command for changing the default service of a URL map."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.third_party.py27 import py27_copy as copy


def _Args(parser):
  """Common arguments to set_default_service commands for each release track."""
  parser.add_argument(
      'name',
      help='The name of the URL map.')


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class SetDefaultServiceGA(base_classes.ReadWriteCommand):
  """Change the default service of a URL map."""

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
  def resource_type(self):
    return 'urlMaps'

  def CreateReference(self, args):
    return self.CreateGlobalReference(args.name)

  def GetGetRequest(self, args):
    """Returns the request for the existing URL map resource."""
    return (self.service,
            'Get',
            self.messages.ComputeUrlMapsGetRequest(
                urlMap=self.ref.Name(),
                project=self.project))

  def GetSetRequest(self, args, replacement, existing):
    return (self.service,
            'Update',
            self.messages.ComputeUrlMapsUpdateRequest(
                urlMap=self.ref.Name(),
                urlMapResource=replacement,
                project=self.project))

  def Modify(self, args, existing):
    """Returns a modified URL map message."""
    replacement = copy.deepcopy(existing)

    default_service_uri = self.CreateGlobalReference(
        args.default_service, resource_type='backendServices').SelfLink()
    replacement.defaultService = default_service_uri

    return replacement


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetDefaultServiceAlpha(SetDefaultServiceGA):
  """Change the default service of a URL map."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--default-service',
        help=('A backend service that will be used for requests for which this '
              'URL map has no mappings.'))
    group.add_argument(
        '--default-backend-bucket',
        help=('A backend bucket that will be used for requests for which this '
              'URL map has no mappings.'))

  def Modify(self, args, existing):
    """Returns a modified URL map message."""
    replacement = copy.deepcopy(existing)

    if args.default_service:
      default_backend_uri = self.CreateGlobalReference(
          args.default_service,
          resource_type='backendServices').SelfLink()
    else:
      default_backend_uri = self.CreateGlobalReference(
          args.default_backend_bucket,
          resource_type='backendBuckets').SelfLink()

    replacement.defaultService = default_backend_uri

    return replacement


SetDefaultServiceGA.detailed_help = {
    'brief': 'Change the default service of a URL map',
    'DESCRIPTION': """\
        *{command}* is used to change the default service of a URL
        map. The default service is used for any requests for which
        there is no mapping in the URL map.
        """,
}
SetDefaultServiceAlpha.detailed_help = {
    'brief': 'Change the default service or default bucket of a URL map',
    'DESCRIPTION': """\
        *{command}* is used to change the default service or default
        bucket of a URL map. The default service or default bucket is
        used for any requests for which there is no mapping in the
        URL map.
        """,
}
