# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Describe command for Threat Prevention profiles."""


from googlecloudsdk.api_lib.network_security.security_profiles import tpp_api
from googlecloudsdk.calliope import base
# sp_flags handles both Organization and Project-level resource arguments.
from googlecloudsdk.command_lib.network_security import sp_flags

_DETAILED_HELP = {
    'DESCRIPTION': """
          Show details of a Threat Prevention Security Profile.

          For more examples, refer to the EXAMPLES section below.
        """,
    'EXAMPLES': """
            To show details of a Threat Prevention security profile named `my-security-profile` in an organization, run:

            $ {command} my-security-profile --organization=1234 --location=global

            To show details of a Threat Prevention security profile named `my-security-profile` in a project, run:

            $ {command} my-security-profile --project=my-project --location=global
        """,
}

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Describe(base.DescribeCommand):
  """Describe a Threat Prevention Security Profile."""

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

    # Returning the full SecurityProfile resource.
    return client.GetSecurityProfile(security_profile.RelativeName())


Describe.detailed_help = _DETAILED_HELP
