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
"""Delete a URL Filtering Security Profile."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.security_profiles import urlf_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'DESCRIPTION': """

          Delete the specified Security Profile.

        """,
    'EXAMPLES': """
          To delete a Security Profile called `my-security-profile` run:

              $ {command} my-security-profile

        """,
}

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Delete(base.DeleteCommand):
  """Delete a URL Filtering Profile."""

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
    client = urlf_api.Client(self.ReleaseTrack(), project_scoped)

    is_async = args.async_

    if not args.quiet:
      delete_warning = 'You are about to delete security_profile [{}]'.format(
          security_profile.Name()
      )
      if not console_io.PromptContinue(message=delete_warning):
        return None

    operation = client.DeleteSecurityProfile(security_profile.RelativeName())

    log.status.Print(
        'Delete request issued for: [{}]'.format(security_profile.Name())
    )

    # Return the in-progress operation if async is requested.
    if is_async:
      log.status.Print(
          'Check operation [{}] for status.'.format(operation.name)
      )
      return operation

    # Default operation poller if async is not specified.
    final_operation = client.WaitForOperation(
        operation_ref=client.GetOperationsRef(operation),
        message='Waiting for operation [{}] to complete'.format(operation.name),
        has_result=False,
    )
    log.status.Print(
        'Deleted security_profile [{}].'.format(security_profile.Name())
    )
    return final_operation
