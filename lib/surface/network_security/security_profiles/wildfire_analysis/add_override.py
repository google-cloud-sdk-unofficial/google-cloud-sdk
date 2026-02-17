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
"""Add override command to a WildFire Analysis profile."""

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
          Add an override to a WildFire Analysis Security Profile.
        """,
    'EXAMPLES': """
          To add an override to a WildFire Analysis Security Profile named
          `my-wf-profile` in organization `1234` with threat-id `12345` and action `ALLOW`, run:

              $ {command} my-wf-profile --organization=1234 --location=global --threat-ids=12345 --action=ALLOW

          To add an override to a WildFire Analysis Security Profile named
          `my-wf-profile` in organization `1234` with wildfire protocol `HTTP` and action `DENY`, run:

              $ {command} my-wf-profile --organization=1234 --location=global --wildfire=HTTP --action=DENY
        """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddOverride(base.UpdateCommand):
  """Add an override to a WildFire Analysis Profile."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    sp_flags.AddSecurityProfileResource(parser, cls.ReleaseTrack())
    parser.add_argument(
        '--action',
        type=str,
        choices=['DEFAULT', 'ALLOW', 'DENY', 'ALERT'],
        required=True,
        help="""The action to take for this override.""",
    )
    override_group = parser.add_mutually_exclusive_group(
        required=True,
        help='Exactly one of these arguments must be specified.',
    )
    override_group.add_argument(
        '--wildfire',
        type=arg_parsers.ArgList(
            choices=['SMTP', 'SMB', 'POP3', 'IMAP', 'HTTP2', 'HTTP', 'FTP']
        ),
        metavar='PROTOCOL',
        help="""Comma-separated list of protocols to override the action for WildFire threats.""",
    )
    override_group.add_argument(
        '--wildfire-inline-ml',
        type=arg_parsers.ArgList(
            choices=['SMTP', 'SMB', 'POP3', 'IMAP', 'HTTP2', 'HTTP', 'FTP']
        ),
        metavar='PROTOCOL',
        help="""Comma-separated list of protocols to override the action for WildFire Inline ML threats.""",
    )
    override_group.add_argument(
        '--threat-ids',
        type=arg_parsers.ArgList(),
        metavar='THREAT_ID',
        help="""Comma-separated list of WildFire Signature IDs to override the action for.""",
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

    if args.threat_ids and args.action not in ['DEFAULT', 'ALLOW', 'DENY']:
      raise exceptions.InvalidArgumentException(
          '--action',
          'Action must be one of DEFAULT, ALLOW, or DENY when --threat-ids is'
          ' specified.',
      )

    response = client.AddOverride(
        security_profile.RelativeName(),
        action=args.action,
        threat_ids=args.threat_ids,
        wildfire_protocols=args.wildfire,
        wildfire_inline_ml_protocols=args.wildfire_inline_ml,
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
