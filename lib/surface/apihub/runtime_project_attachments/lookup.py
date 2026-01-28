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
"""Lookup Runtime Project Attachment command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Lookup(base.DescribeCommand):
  """Lookup a runtime project attachment."""

  detailed_help = {
      'DESCRIPTION': (
          """
          Lookup a runtime project attachment.
          """
      ),
      'EXAMPLES': (
          """
          To lookup a runtime project attachment for a specific service project, run:

            $ {command} --service-project=my-service-project --location=us-central1
          """
      ),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--service-project',
        required=True,
        help='The service project ID to lookup attachment for.',
    )
    parser.add_argument(
        '--location',
        required=True,
        help='The location of the runtime project attachment.',
    )

  def Run(self, args):
    """Run the lookup command."""
    client = apis.GetClientInstance('apihub', 'v1')
    messages = apis.GetMessagesModule('apihub', 'v1')

    # Construct the name (Runtime Project Location)
    # Format: projects/{project}/locations/{location}
    # We use the 'service-project' as the project in the name.

    # We can use resources.REGISTRY or manual string construction.
    # Manual is safer if we don't have a specific collection for
    # "Runtime Project Location", but 'apihub.projects.locations' works.

    location_ref = resources.REGISTRY.Parse(
        args.location,
        params={'projectsId': args.service_project},
        collection='apihub.projects.locations',
    )

    # Use getattr to avoid static lint errors for dynamic message attributes
    request_type = getattr(
        messages, 'ApihubProjectsLocationsLookupRuntimeProjectAttachmentRequest'
    )
    request = request_type(name=location_ref.RelativeName())

    return client.projects_locations.LookupRuntimeProjectAttachment(request)
