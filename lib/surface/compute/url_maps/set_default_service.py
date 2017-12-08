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

import copy

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.backend_buckets import (
    flags as backend_bucket_flags)
from googlecloudsdk.command_lib.compute.backend_services import (
    flags as backend_service_flags)
from googlecloudsdk.command_lib.compute.url_maps import flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetDefaultServiceGA(base_classes.ReadWriteCommand):
  """Change the default service of a URL map."""

  BACKEND_SERVICE_ARG = None
  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForUrlMap())
    cls.BACKEND_SERVICE_ARG.AddArgument(parser)
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser)

  @property
  def service(self):
    return self.compute.urlMaps

  @property
  def resource_type(self):
    return 'urlMaps'

  def CreateReference(self, args):
    return self.URL_MAP_ARG.ResolveAsResource(args, self.resources)

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

    replacement.defaultService = self.BACKEND_SERVICE_ARG.ResolveAsResource(
        args, self.resources).SelfLink()

    return replacement


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class SetDefaultServiceBeta(SetDefaultServiceGA):
  """Change the default service of a URL map."""

  BACKEND_BUCKET_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.BACKEND_BUCKET_ARG = (
        backend_bucket_flags.BackendBucketArgumentForUrlMap(required=False))
    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForUrlMap(required=False))
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser)

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
      default_backend_uri = self.BACKEND_SERVICE_ARG.ResolveAsResource(
          args, self.resources).SelfLink()
    else:
      default_backend_uri = self.BACKEND_BUCKET_ARG.ResolveAsResource(
          args, self.resources).SelfLink()

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
SetDefaultServiceBeta.detailed_help = {
    'brief': 'Change the default service or default bucket of a URL map',
    'DESCRIPTION': """\
        *{command}* is used to change the default service or default
        bucket of a URL map. The default service or default bucket is
        used for any requests for which there is no mapping in the
        URL map.
        """,
}
