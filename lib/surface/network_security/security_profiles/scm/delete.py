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
"""Delete an SCM Security Profile."""

from googlecloudsdk.api_lib.network_security.security_profiles import scm_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'DESCRIPTION': """

          Delete the specified SCM Security Profile.

        """,
    'EXAMPLES': """
          To delete an SCM Security Profile called `my-scm-security-profile` in organization `1234` and location `global`, run:

              $ {command} my-scm-security-profile --organization=1234 --location=global

        """,
}

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete an SCM Profile."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    project_scope_supported = (
        cls.ReleaseTrack() in _PROJECT_SCOPE_SUPPORTED_TRACKS
    )
    sp_flags.AddSecurityProfileResource(
        parser, cls.ReleaseTrack(), project_scope_supported
    )
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, False)

  def Run(self, args):
    result = args.CONCEPTS.security_profile.Parse()
    security_profile = result.result

    project_scoped = (
        result.concept_type.name
        == sp_flags.PROJECT_SECURITY_PROFILE_RESOURCE_COLLECTION
    )
    client = scm_api.Client(self.ReleaseTrack(), project_scoped)

    is_async = args.async_

    if not args.quiet:
      delete_warning = (
          'You are about to delete security_profile'
          f' [{security_profile.Name()}]'
      )
      if not console_io.PromptContinue(message=delete_warning):
        return None

    operation = client.DeleteSecurityProfile(security_profile.RelativeName())

    log.status.Print(
        f'Delete request issued for: [{security_profile.Name()}]'
    )

    # Return the in-progress operation if async is requested.
    if is_async:
      log.status.Print(f'Check operation [{operation.name}] for status.')
      return operation

    # Default operation poller if async is not specified.
    final_operation = client.WaitForOperation(
        operation_ref=client.GetOperationsRef(operation),
        message=f'Waiting for operation [{operation.name}] to complete',
        has_result=False,
    )
    log.status.Print(f'Deleted security_profile [{security_profile.Name()}].')
    return final_operation
