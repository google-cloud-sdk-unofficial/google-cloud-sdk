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
"""Delete Override command to delete existing overrides of threat prevention profile overrides."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.security_profiles.threat_prevention import sp_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags
from googlecloudsdk.core import exceptions as core_exceptions

DETAILED_HELP = {
    'DESCRIPTION': """
          To delete existing severities or threat-ids of
          threat prevention profile.
          Check the updates of update-override command by using `gcloud network-security
          security-profiles threat-prevention list-override my-security-profile`.

          For more examples, refer to the EXAMPLES section below.

        """,
    'EXAMPLES': """
            To update an override, run:

              $ {command} my-security-profile --severities=MEDIUM

            `my-security-profile` is the name of the Security Profile in the
            format organizations/{organizationID}/locations/{location}/securityProfiles/
            {security_profile_id}
            where organizationID is the organization ID to which the changes should apply,
            location either global or region specified and
            security_profile_id the Security Profile Identifier

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteOverride(base.UpdateCommand):
  """Delete overrides of Threat Prevention Profile."""

  @staticmethod
  def Args(parser):
    sp_flags.AddSecurityProfileResource(parser)
    sp_flags.AddSeverityorThreatIDArg(parser, required=True)

  def Run(self, args):
    client = sp_api.Client(self.ReleaseTrack())
    security_profile = args.CONCEPTS.security_profile.Parse()

    update_mask = ''
    overrides = []

    if args.IsSpecified('severities'):
      update_mask = 'severityOverrides'
      overrides = args.severities
    elif args.IsSpecified('threat_ids'):
      update_mask = 'threatOverrides'
      overrides = args.threat_ids
    else:
      raise core_exceptions.Error(
          'Either --severities or --threat-ids must be specified'
      )

    return client.DeleteOverride(
        security_profile.RelativeName(),
        overrides,
        update_mask,
    )


DeleteOverride.detailed_help = DETAILED_HELP
