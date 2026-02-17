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
"""Describe command to describe a security profile group."""

from googlecloudsdk.api_lib.network_security.security_profile_groups import spg_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import spg_flags

_DETAILED_HELP = {
    'DESCRIPTION': """

          Show details of a Security Profile Group.

        """,
    'EXAMPLES': """
          To show details of a Security Profile Group named `my-security-profile-group` run:

              $ {command} my-security-profile-group --organization=1234 --location=global

        """,
}

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class DescribeProfileGroup(base.DescribeCommand):
  """Describe a Security Profile Group."""

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    spg_flags.AddSecurityProfileGroupResource(
        parser, cls.ReleaseTrack(), project_scope_supported
    )

  def Run(self, args):
    result = args.CONCEPTS.security_profile_group.Parse()
    security_profile_group = result.result

    project_scoped = (
        result.concept_type.name
        == spg_flags.PROJECT_SECURITY_PROFILE_GROUP_RESOURCE_COLLECTION
    )
    client = spg_api.Client(self.ReleaseTrack(), project_scoped)

    return client.GetSecurityProfileGroup(
        security_profile_group_name=security_profile_group.RelativeName(),
    )


DescribeProfileGroup.detailed_help = _DETAILED_HELP
