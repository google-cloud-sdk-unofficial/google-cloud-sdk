# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Create command to create a new resource of security profile group."""

import types

from googlecloudsdk.api_lib.network_security.security_profile_groups import spg_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import spg_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': """

          Create a new Security Profile Group with the given name.

        """,
    'EXAMPLES': """
          To create a Security Profile Group with the name `my-security-profile-group`, with a threat prevention profile using `--threat-prevention-profile` flag and optional description as `optional description`, run:

              $ {command} my-security-profile-group --organization=1234 --location=global --threat-prevention-profile=`organizations/1234/locations/global/securityProfiles/my-security-profile` --description='optional description'

        """,
}

_URL_FILTERING_SUPPORTED = (
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA
)

_WILDFIRE_ANALYSIS_SUPPORTED = (
    base.ReleaseTrack.ALPHA,
)

_SUPPORTED_PROFILES = (
    'threat_prevention_profile',
    'url_filtering_profile',
    'wildfire_analysis_profile',
    'custom_mirroring_profile',
    'custom_intercept_profile',
)

_INCOMPATIBLE_PAIRS = (
    ('threat_prevention_profile', 'custom_mirroring_profile'),
    ('threat_prevention_profile', 'custom_intercept_profile'),
    ('url_filtering_profile', 'custom_mirroring_profile'),
    ('url_filtering_profile', 'custom_intercept_profile'),
    ('wildfire_analysis_profile', 'custom_mirroring_profile'),
    ('wildfire_analysis_profile', 'custom_intercept_profile'),
    ('custom_mirroring_profile', 'custom_intercept_profile'),
)

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class CreateProfileGroup(base.CreateCommand):
  """Create a new Security Profile Group."""

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    spg_flags.AddSecurityProfileGroupResource(
        parser, cls.ReleaseTrack(), project_scope_supported
    )
    spg_flags.AddProfileGroupDescription(parser)
    required_group = parser.add_group(required=True)
    # TODO: b/349671332 - Remove this conditional once the group is released.
    if cls.ReleaseTrack() in _URL_FILTERING_SUPPORTED:
      spg_flags.AddSecurityProfileResource(
          parser,
          cls.ReleaseTrack(),
          'url-filtering-profile',
          group=required_group,
          required=False,
          help_text='Path to URL Filtering Profile resource.',
          project_scope_supported=project_scope_supported,
      )
    # TODO: b/399684751 - Remove this conditional once the group is released.
    if cls.ReleaseTrack() in _WILDFIRE_ANALYSIS_SUPPORTED:
      spg_flags.AddSecurityProfileResource(
          parser,
          cls.ReleaseTrack(),
          'wildfire-analysis-profile',
          group=required_group,
          required=False,
          help_text='Path to Wildfire Analysis Profile resource.',
          project_scope_supported=project_scope_supported,
      )
    spg_flags.AddSecurityProfileResource(
        parser,
        cls.ReleaseTrack(),
        'threat-prevention-profile',
        group=required_group,
        required=False,
        arg_aliases=['security-profile'],
        help_text='Path to Threat Prevention Profile resource.',
        project_scope_supported=project_scope_supported,
    )
    spg_flags.AddSecurityProfileResource(
        parser,
        cls.ReleaseTrack(),
        'custom-mirroring-profile',
        group=required_group,
        required=False,
        help_text='Path to Custom Mirroring Profile resource.',
        project_scope_supported=project_scope_supported,
    )
    spg_flags.AddSecurityProfileResource(
        parser,
        cls.ReleaseTrack(),
        'custom-intercept-profile',
        group=required_group,
        required=False,
        help_text='Path to Custom Intercept Profile resource.',
        project_scope_supported=project_scope_supported,
    )
    labels_util.AddCreateLabelsFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, False)

  def Run(self, args):
    result = args.CONCEPTS.security_profile_group.Parse()
    security_profile_group = result.result

    profiles = self.ParseAndValidateSecurityProfiles(args)

    project_scoped = (
        result.concept_type.name
        == spg_flags.PROJECT_SECURITY_PROFILE_GROUP_RESOURCE_COLLECTION
    )
    client = spg_api.Client(self.ReleaseTrack(), project_scoped)

    description = args.description
    is_async = args.async_
    labels = labels_util.ParseCreateArgs(
        args, client.messages.SecurityProfileGroup.LabelsValue
    )
    safe_relative_name = (
        lambda profile: profile.RelativeName() if profile is not None else None
    )

    response = client.CreateSecurityProfileGroup(
        security_profile_group_name=security_profile_group.RelativeName(),
        security_profile_group_id=security_profile_group.Name(),
        parent=security_profile_group.Parent().RelativeName(),
        description=description,
        threat_prevention_profile=safe_relative_name(
            profiles.threat_prevention_profile
        ),
        url_filtering_profile=safe_relative_name(
            profiles.url_filtering_profile
        ),
        wildfire_analysis_profile=safe_relative_name(
            profiles.wildfire_analysis_profile
        ),
        custom_mirroring_profile=safe_relative_name(
            profiles.custom_mirroring_profile
        ),
        custom_intercept_profile=safe_relative_name(
            profiles.custom_intercept_profile
        ),
        labels=labels,
    )

    # Return the in-progress operation if async is requested.
    if is_async:
      operation_id = response.name
      log.status.Print(
          'Check for operation completion status using operation ID:',
          operation_id,
      )
      return response

    # Default operation poller if async is not specified.
    return client.WaitForOperation(
        operation_ref=client.GetOperationsRef(response),
        message='Waiting for security-profile-group [{}] to be created'.format(
            security_profile_group.RelativeName()
        ),
        has_result=True,
    )

  def ParseAndValidateSecurityProfiles(self, args):
    """Parses and validates security profiles from args."""
    profiles = {}

    for supported_profile in _SUPPORTED_PROFILES:
      profiles[supported_profile] = None
      if getattr(args, supported_profile, None):
        result = getattr(args.CONCEPTS, supported_profile).Parse()
        profiles[supported_profile] = result.result

    for pair in _INCOMPATIBLE_PAIRS:
      if profiles[pair[0]] and profiles[pair[1]]:
        raise core_exceptions.Error(
            'Only one of the following profiles can be specified at the same'
            ' time: %s'
            % ', '.join(pair).replace('_', '-')
        )
    return types.SimpleNamespace(**profiles)


CreateProfileGroup.detailed_help = _DETAILED_HELP
