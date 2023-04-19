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
"""Create command to create a new resource of threat prevention profile."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.security_profiles.threat_prevention import sp_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags

DETAILED_HELP = {
    'DESCRIPTION': """

          Create a new Security Profile with the given name.

        """,
    'EXAMPLES': """
          To create a Security Profile with the name `my-security-profile` which includes location as global or region specifed and organization ID, optional description as `New Security Profile`, run:

              $ {command} my-security-profile  --description="New Security Profile"

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateProfile(base.CreateCommand):
  """Create a new Threat Prevention Profile."""

  @staticmethod
  def Args(parser):
    sp_flags.AddSecurityProfileResource(parser)
    sp_flags.AddProfileDescription(parser)

  def Run(self, args):
    client = sp_api.Client(self.ReleaseTrack())
    security_profile = args.CONCEPTS.security_profile.Parse()
    description = args.description

    if not args.IsSpecified('description'):
      args.description = 'Security Profile of type Threat Prevention'

    return client.CreateSecurityProfile(
        name=security_profile.RelativeName(),
        sp_id=security_profile.Name(),
        parent=security_profile.Parent().RelativeName(),
        description=description)

CreateProfile.detailed_help = DETAILED_HELP
