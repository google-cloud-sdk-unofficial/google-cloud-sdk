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
"""Add inline ml exception command to a WildFire Analysis profile."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.security_profiles import wildfire_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
          Add a WildFire inline machine learning exception to a WildFire Analysis Security Profile.
        """,
    'EXAMPLES': """
          To add an inline machine learning exception to a WildFire Analysis Security Profile named
          `my-wf-profile` in organization `1234` with partial-hash `12345abcdef`, run:

              $ {command} my-wf-profile --organization=1234 --location=global --partial-hash=12345abcdef

          To add an inline machine learning exception to a WildFire Analysis Security Profile named
          `my-wf-profile` in organization `1234` with partial-hash `12345abcdef` and filename `virus.exe`, run:

              $ {command} my-wf-profile --organization=1234 --location=global --partial-hash=12345abcdef --filename=virus.exe
        """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddInlineMlException(base.UpdateCommand):
  """Add a WildFire inline machine learning exception to a WildFire Analysis Profile."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    sp_flags.AddSecurityProfileResource(parser, cls.ReleaseTrack())
    parser.add_argument(
        '--partial-hash',
        type=str,
        required=True,
        help="""Machine learning partial hash of the file.""",
    )
    parser.add_argument(
        '--filename',
        type=str,
        required=False,
        help="""Name of the file.""",
    )
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, False)

  def Run(self, args):
    client = wildfire_api.Client(self.ReleaseTrack())
    result = args.CONCEPTS.security_profile.Parse()
    security_profile = result.result
    is_async = args.async_

    if args.location != 'global':
      raise core_exceptions.Error(
          'Only `global` location is supported, but got: %s' % args.location
      )

    response = client.AddInlineMlException(
        security_profile.RelativeName(),
        partial_hash=args.partial_hash,
        filename=args.filename,
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
        message='Waiting for security-profile [{}] to be updated'.format(
            security_profile.RelativeName()
        ),
        has_result=True,
    )
