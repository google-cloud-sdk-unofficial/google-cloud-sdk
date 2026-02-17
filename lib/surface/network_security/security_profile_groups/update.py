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
"""Update command to update a security profile group resource."""

import types

from googlecloudsdk.api_lib.network_security.security_profile_groups import spg_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import spg_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

_detailed_help = {
    'DESCRIPTION': """

          Update details of a Security Profile Group.

        """,
    'EXAMPLES': """
          To update a Security Profile Group with new threat prevention profile `my-new-security-profile`, run:

              $ {command} my-security-profile-group --organization=1234 --location=global --threat-prevention-profile=`organizations/1234/locations/global/securityProfiles/my-new-security-profile` --description='New Security Profile of type threat prevention'

        """,
}

_URL_FILTERING_SUPPORTED = (
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA
)

_WILDFIRE_ANALYSIS_SUPPORTED = (
    base.ReleaseTrack.ALPHA,
)

_SUPPORTED_PROFILES = [
    'threat_prevention_profile',
    'url_filtering_profile',
    'wildfire_analysis_profile',
]

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class UpdateProfileGroup(base.UpdateCommand):
  """Update a Security Profile Group."""

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    spg_flags.AddSecurityProfileGroupResource(
        parser, cls.ReleaseTrack(), project_scope_supported
    )
    spg_flags.AddProfileGroupDescription(parser)
    # TODO: b/349671332 - Remove this conditional once the group is released.
    threat_prevention_group = None
    if cls.ReleaseTrack() in _URL_FILTERING_SUPPORTED:
      threat_prevention_group = parser.add_group(mutex=True)
      threat_prevention_group.add_argument(
          '--clear-threat-prevention-profile',
          action='store_true',
          help='''\
            Clear the threat-prevention-profile field.
          ''',
      )
    spg_flags.AddSecurityProfileResource(
        parser,
        cls.ReleaseTrack(),
        'threat-prevention-profile',
        group=threat_prevention_group,
        required=False,
        arg_aliases=['security-profile'],
        help_text='Path to Threat Prevention Profile resource.',
        project_scope_supported=project_scope_supported,
    )
    # TODO: b/349671332 - Remove this conditional once the group is released.
    if cls.ReleaseTrack() in _URL_FILTERING_SUPPORTED:
      url_filtering_group = parser.add_group(mutex=True)
      url_filtering_group.add_argument(
          '--clear-url-filtering-profile',
          action='store_true',
          help='''\
            Clear the url-filtering-profile field.
          ''',
      )
      spg_flags.AddSecurityProfileResource(
          parser,
          cls.ReleaseTrack(),
          'url-filtering-profile',
          group=url_filtering_group,
          required=False,
          help_text='Path to URL Filtering Profile resource.',
          project_scope_supported=project_scope_supported,
      )
    if cls.ReleaseTrack() in _WILDFIRE_ANALYSIS_SUPPORTED:
      wildfire_analysis_group = parser.add_group(mutex=True)
      wildfire_analysis_group.add_argument(
          '--clear-wildfire-analysis-profile',
          action='store_true',
          help='''\
            Clear the wildfire-analysis-profile field.
          ''',
      )
      spg_flags.AddSecurityProfileResource(
          parser,
          cls.ReleaseTrack(),
          'wildfire-analysis-profile',
          group=wildfire_analysis_group,
          required=False,
          help_text='Path to Wildfire Analysis Profile resource.',
      )
    labels_util.AddUpdateLabelsFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, False)

  def getLabel(self, client, security_profile_group):
    return client.GetSecurityProfileGroup(
        security_profile_group.RelativeName()
    ).labels

  def Run(self, args):
    result = args.CONCEPTS.security_profile_group.Parse()
    security_profile_group = result.result

    profiles = self.ParseSecurityProfiles(args)
    description = args.description
    is_async = args.async_

    project_scoped = (
        result.concept_type.name
        == spg_flags.PROJECT_SECURITY_PROFILE_GROUP_RESOURCE_COLLECTION
    )
    client = spg_api.Client(self.ReleaseTrack(), project_scoped)

    labels_update = labels_util.ProcessUpdateArgsLazy(
        args,
        client.messages.SecurityProfileGroup.LabelsValue,
        orig_labels_thunk=lambda: self.getLabel(client, security_profile_group),
    )

    update_mask = []
    if (profiles.threat_prevention_profile is not None
        or self.ReleaseTrack() in _URL_FILTERING_SUPPORTED
        and args.clear_threat_prevention_profile):
      update_mask.append('threatPreventionProfile')
    if (profiles.url_filtering_profile is not None
        or self.ReleaseTrack() in _URL_FILTERING_SUPPORTED
        and args.clear_url_filtering_profile):
      update_mask.append('urlFilteringProfile')
    if (profiles.wildfire_analysis_profile is not None
        or self.ReleaseTrack() in _WILDFIRE_ANALYSIS_SUPPORTED
        and args.clear_wildfire_analysis_profile):
      update_mask.append('wildfireAnalysisProfile')

    if description is not None:
      update_mask.append('description')

    if not update_mask:
      raise core_exceptions.Error(
          'Operation failed to satisfy minimum qualification. Please specify'
          ' the attribute which needs an update. `description` and/or `security'
          ' profile` can be updated.'
      )

    response = client.UpdateSecurityProfileGroup(
        security_profile_group_name=security_profile_group.RelativeName(),
        description=description if description is not None else None,
        threat_prevention_profile=profiles.threat_prevention_profile.RelativeName()
        if profiles.threat_prevention_profile is not None
        else None,
        url_filtering_profile=profiles.url_filtering_profile.RelativeName()
        if profiles.url_filtering_profile is not None
        else None,
        wildfire_analysis_profile=profiles.wildfire_analysis_profile.RelativeName()
        if profiles.wildfire_analysis_profile is not None
        else None,
        update_mask=','.join(update_mask),
        labels=labels_update.GetOrNone(),
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
        message='Waiting for security-profile-group [{}] to be updated'.format(
            security_profile_group.RelativeName()
        ),
        has_result=True,
    )

  def ParseSecurityProfiles(self, args):
    """Parses security profiles from args."""
    profiles = {}

    for supported_profile in _SUPPORTED_PROFILES:
      profiles[supported_profile] = None
      if getattr(args, supported_profile, None):
        result = getattr(args.CONCEPTS, supported_profile).Parse()
        profiles[supported_profile] = result.result

    return types.SimpleNamespace(**profiles)


UpdateProfileGroup.detailed_help = _detailed_help
