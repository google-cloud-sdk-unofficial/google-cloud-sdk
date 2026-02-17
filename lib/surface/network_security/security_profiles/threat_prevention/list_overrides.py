# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""List Overrides command to list existing overrides of threat prevention profile."""

from googlecloudsdk.api_lib.network_security.security_profiles import tpp_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags

DETAILED_HELP = {
    'DESCRIPTION': """
          To list existing antivirus, severities, or threat-ids of
          threat prevention profile.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To list overrides, run:

              $ {command} my-security-profile

            `my-security-profile` is the name of the Security Profile in the
            format organizations/{organizationID}/locations/{location}/securityProfiles/
            {security_profile_id}
            where organizationID is the organization ID to which the changes should apply,
            location - `global` specified and
            security_profile_id the Security Profile Identifier

        """,
}

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.DefaultUniverseOnly
class ListOverrides(base.DescribeCommand):
  """List overrides of Threat Prevention Profile."""

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    sp_flags.AddSecurityProfileResource(
        parser, cls.ReleaseTrack(), project_scope_supported
    )

  def Run(self, args):
    result = args.CONCEPTS.security_profile.Parse()
    security_profile = result.result

    project_scoped = (
        result.concept_type.name
        == sp_flags.PROJECT_SECURITY_PROFILE_RESOURCE_COLLECTION
    )
    client = tpp_api.Client(self.ReleaseTrack(), project_scoped)

    return client.ListOverrides(security_profile.RelativeName())


ListOverrides.detailed_help = DETAILED_HELP
