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
"""Delete inline cloud analysis rule command from a WildFire Analysis profile."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.security_profiles import wildfire_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.network_security import sp_flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
          Delete a WildFire inline cloud analysis rule from a WildFire Analysis Security Profile.
        """,
    'EXAMPLES': """
          To delete an inline cloud analysis rule from a WildFire Analysis Security Profile named
          `my-wf-profile` in organization `1234` with file-types `ANY_FILE`,
          direction `BOTH`, and action `ALLOW`, run:

              $ {command} my-wf-profile --organization=1234 --location=global --file-types=ANY_FILE --direction=BOTH --action=ALLOW
        """,
}

FILE_TYPE_CHOICES = [
    'ANY_FILE',
    'PE',
]


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteInlineCloudAnalysisRule(base.UpdateCommand):
  """Delete a WildFire inline cloud analysis rule from a WildFire Analysis Profile."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    sp_flags.AddSecurityProfileResource(parser, cls.ReleaseTrack())
    parser.add_argument(
        '--file-types',
        type=arg_parsers.ArgList(),
        required=True,
        metavar='FILE_TYPE',
        help="""Types of files that will be submitted to WildFire for analysis.
FILE_TYPE must be one of: {0}.
If ANY_FILE is specified, no other types can be specified.""".format(
            ', '.join(FILE_TYPE_CHOICES)
        ),
    )
    parser.add_argument(
        '--direction',
        type=str,
        choices=['UPLOAD', 'DOWNLOAD', 'BOTH'],
        required=True,
        help="""Direction of traffic that will be checked for files to submit to WildFire.""",
    )
    parser.add_argument(
        '--action',
        type=str,
        choices=['ALLOW', 'DENY', 'ALERT'],
        required=True,
        help="""Action to take when Inline Cloud Analysis detects a threat.""",
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

    file_types_upper = []
    for ft in args.file_types:
      ft_upper = ft.upper()
      if ft_upper not in FILE_TYPE_CHOICES:
        raise exceptions.InvalidArgumentException(
            '--file-types',
            'Invalid file type: {0}. Must be one of {1}'.format(
                ft, ', '.join(FILE_TYPE_CHOICES)
            ),
        )
      file_types_upper.append(ft_upper)

    # If ANY_FILE is specified, no other file types can be specified.
    if 'ANY_FILE' in file_types_upper and len(file_types_upper) > 1:
      raise exceptions.InvalidArgumentException(
          '--file-types',
          'If ANY_FILE is specified, no other file types can be specified.',
      )

    response = client.DeleteInlineCloudAnalysisRule(
        security_profile.RelativeName(),
        file_types_upper=file_types_upper,
        direction=args.direction,
        action=args.action,
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
