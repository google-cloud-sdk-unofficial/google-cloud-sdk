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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

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

_CUSTOM_MIRRORING_SUPPORTED = (
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
)
_CUSTOM_INTERCEPT_SUPPORTED = (base.ReleaseTrack.ALPHA,)


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class CreateProfileGroup(base.CreateCommand):
  """Create a new Security Profile Group."""

  @classmethod
  def Args(cls, parser):
    spg_flags.AddSecurityProfileGroupResource(parser, cls.ReleaseTrack())
    spg_flags.AddProfileGroupDescription(parser)
    spg_flags.AddSecurityProfileResource(
        parser,
        cls.ReleaseTrack(),
        'threat-prevention-profile',
        required=False,
        arg_aliases=['security-profile'],
    )
    if cls.ReleaseTrack() in _CUSTOM_MIRRORING_SUPPORTED:
      spg_flags.AddSecurityProfileResource(
          parser, cls.ReleaseTrack(), 'custom-mirroring-profile', required=False
      )
    if cls.ReleaseTrack() in _CUSTOM_INTERCEPT_SUPPORTED:
      spg_flags.AddSecurityProfileResource(
          parser, cls.ReleaseTrack(), 'custom-intercept-profile', required=False
      )
    labels_util.AddCreateLabelsFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, False)

  def Run(self, args):
    client = spg_api.Client(self.ReleaseTrack())
    self.ValidateCompatibleProfiles(args)
    security_profile_group = args.CONCEPTS.security_profile_group.Parse()
    threat_prevention_profile = args.CONCEPTS.threat_prevention_profile.Parse()
    custom_mirroring_profile = (
        args.CONCEPTS.custom_mirroring_profile.Parse()
        if hasattr(args.CONCEPTS, 'custom_mirroring_profile')
        else None
    )
    custom_intercept_profile = (
        args.CONCEPTS.custom_intercept_profile.Parse()
        if hasattr(args.CONCEPTS, 'custom_intercept_profile')
        else None
    )

    description = args.description
    is_async = args.async_
    labels = labels_util.ParseCreateArgs(
        args, client.messages.SecurityProfileGroup.LabelsValue
    )

    if security_profile_group.locationsId != 'global':
      raise core_exceptions.Error(
          'Only `global` location is supported, but got: %s'
          % security_profile_group.locationsId
      )

    response = client.CreateSecurityProfileGroup(
        security_profile_group_name=security_profile_group.RelativeName(),
        security_profile_group_id=security_profile_group.Name(),
        parent=security_profile_group.Parent().RelativeName(),
        description=description,
        threat_prevention_profile=threat_prevention_profile.RelativeName()
        if threat_prevention_profile is not None
        else None,
        custom_mirroring_profile=custom_mirroring_profile.RelativeName()
        if custom_mirroring_profile is not None
        else None,
        custom_intercept_profile=custom_intercept_profile.RelativeName()
        if custom_intercept_profile is not None
        else None,
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

  # TODO: b/353974844 - remove hasattr checks once custom_mirroring and
  # custom_intercept profiles are fully rolled out to v1.
  def ValidateCompatibleProfiles(self, args):
    profiles = []
    if args.CONCEPTS.threat_prevention_profile.Parse() is not None:
      profiles.append('threat-prevention-profile')
    if (
        hasattr(args.CONCEPTS, 'custom_mirroring_profile')
        and args.CONCEPTS.custom_mirroring_profile.Parse() is not None
    ):
      profiles.append('custom-mirroring-profile')
    if (
        hasattr(args.CONCEPTS, 'custom_intercept_profile')
        and args.CONCEPTS.custom_intercept_profile.Parse() is not None
    ):
      profiles.append('custom-intercept-profile')

    # TODO: b/349673860 - when adding domain_filter profile, expand the check
    # here to allow TPP+DF.
    if len(profiles) > 1:
      raise core_exceptions.Error(
          'Only one of the following profiles can be specified at the same'
          ' time: %s'
          % ', '.join(profiles)
      )


CreateProfileGroup.detailed_help = _DETAILED_HELP
