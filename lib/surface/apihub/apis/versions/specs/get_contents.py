# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Get Spec Contents command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetContents(base.DescribeCommand):
  """Get the contents of a spec."""

  detailed_help = {
      'DESCRIPTION': (
          """
          Get the contents of a spec.
          """
      ),
      'EXAMPLES': (
          """
          To get the contents of a spec, run:

            $ {command} SPEC --api=API --version=VERSION --location=LOCATION
          """
      ),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    # Register resource args for the spec
    # usually done via concept parsers, but for simple manual command we can use
    # positional/flags. However, to match consistency, we should try to reuse
    # existing resource args if possible.
    # For now, explicit flags/arguments to match the path:
    # projects/{project}/locations/{location}/apis/{api}/versions/{version}/specs/{spec}

    parser.add_argument('spec', help='The spec ID.')
    parser.add_argument('--api', required=True, help='The API ID.')
    parser.add_argument('--version', required=True, help='The version ID.')
    parser.add_argument('--location', required=True, help='The location ID.')

  def Run(self, args):
    """Run the get-contents command."""
    # Use generic client logic if specific api_lib is not available
    client = apis.GetClientInstance('apihub', 'v1')
    messages = apis.GetMessagesModule('apihub', 'v1')

    project = properties.VALUES.core.project.Get(required=True)

    # Construct resource name
    # projects/{project}/locations/{location}/apis/{api}/versions/{version}/specs/{spec}
    spec_ref = resources.REGISTRY.Parse(
        args.spec,
        params={
            'projectsId': project,
            'locationsId': args.location,
            'apisId': args.api,
            'versionsId': args.version,
        },
        collection='apihub.projects.locations.apis.versions.specs',
    )

    # Use getattr to avoid static lint errors for dynamic message attributes
    request_type = getattr(
        messages, 'ApihubProjectsLocationsApisVersionsSpecsGetContentsRequest'
    )
    request = request_type(name=spec_ref.RelativeName())

    return client.projects_locations_apis_versions_specs.GetContents(request)
