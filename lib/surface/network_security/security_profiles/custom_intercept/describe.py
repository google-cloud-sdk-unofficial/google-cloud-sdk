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
"""Describe a Custom Intercept Security Profile."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.security_profiles import intercept_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags

DETAILED_HELP = {
    'DESCRIPTION': """

          Show details of the Security Profile.

        """,
    'EXAMPLES': """
          To show details of a Security Profile named `my-intercept-sp` run:

              $ {command} my-intercept-sp --organization=1234 --location=global

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
  """Describe a Custom Intercept Profile."""

  detailed_help = DETAILED_HELP

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
    client = intercept_api.Client(self.ReleaseTrack(), project_scoped)

    return client.GetSecurityProfile(security_profile.RelativeName())
