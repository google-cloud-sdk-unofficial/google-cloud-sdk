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
"""List URL Filtering Profiles command."""

from googlecloudsdk.api_lib.network_security.security_profiles import urlf_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags

DETAILED_HELP = {
    'DESCRIPTION': """
          List URL Filtering Security Profiles.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To list URL Filtering security profiles in an organization, run:

            $ {command} --organization=12345 --location=global

        """,
}

_FORMAT = """\
table(
    name.basename():label=NAME
)
"""

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List URL Filtering Security Profiles."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(sp_flags.MakeGetUriFunc(cls.ReleaseTrack()))
    sp_flags.AddLocationResourceArg(
        parser=parser,
        help_text='Parent resource for the list operation.',
        required=True,
        project_scope_supported=project_scope_supported,
    )

  def Run(self, args):

    result = args.CONCEPTS.location.Parse()
    parent_ref = result.result

    project_scoped = (
        result.concept_type.name
        == sp_flags.PROJECT_LOCATION_RESOURCE_COLLECTION
    )
    client = urlf_api.Client(self.ReleaseTrack(), project_scoped)

    return client.ListUrlFilteringProfiles(
        parent_ref.RelativeName(), page_size=args.page_size
    )
