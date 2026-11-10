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
"""Create command to create a new resource of SCM profile."""

from googlecloudsdk.api_lib.network_security.security_profiles import scm_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """

          Create a new SCM Security Profile.

        """,
    'EXAMPLES': """
          To create an SCM Security Profile named `my-scm-security-profile` in organization `1234` and location `global` with an optional description as `New SCM Security Profile`, run:

              $ {command} my-scm-security-profile --organization=1234 --location=global --description="New SCM Security Profile"

        """,
}

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a new SCM Profile."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    sp_flags.AddSecurityProfileResource(
        parser, cls.ReleaseTrack(), project_scope_supported
    )
    sp_flags.AddProfileDescription(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, False)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    result = args.CONCEPTS.security_profile.Parse()
    security_profile = result.result

    project_scoped = (
        result.concept_type.name
        == sp_flags.PROJECT_SECURITY_PROFILE_RESOURCE_COLLECTION
    )
    client = scm_api.Client(self.ReleaseTrack(), project_scoped)

    description = args.description
    labels = labels_util.ParseCreateArgs(
        args, client.messages.SecurityProfile.LabelsValue
    )
    is_async = args.async_

    response = client.CreateScmProfile(
        sp_id=security_profile.Name(),
        parent=security_profile.Parent().RelativeName(),
        description=description,
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
        message=(
            'Waiting for security-profile'
            f' [{security_profile.RelativeName()}] to be created'
        ),
        has_result=True,
    )
