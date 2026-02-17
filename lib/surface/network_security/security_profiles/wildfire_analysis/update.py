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
"""Update command to update WildFire Analysis profile."""

from googlecloudsdk.api_lib.network_security.security_profiles import wildfire_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
          Update a security profile of type WildFire Analysis.
        """,
    'EXAMPLES': """
          To update a WildFire Analysis security-profile `my-wildfire-security-profile` with
          organization 1234, location global, and project my-project, run:

          $ {command} my-wildfire-security-profile --organization=1234 --location=global --project=my-project --no-wildfire-realtime-lookup --analyze-windows-executables --no-analyze-shell
        """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update a WildFire Analysis Security Profile."""

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    sp_flags.AddSecurityProfileResource(parser, cls.ReleaseTrack())
    sp_flags.AddProfileDescription(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, False)
    # StoreTrueFalseAction is used to support both "--field" and "--no-field".
    parser.add_argument(
        '--wildfire-realtime-lookup',
        action=arg_parsers.StoreTrueFalseAction,
        help=(
            'Hold the transfer of a file while the WildFire real-time signature'
            ' cloud performs a signature lookup.'
        ),
    )
    parser.add_argument(
        '--analyze-windows-executables',
        action=arg_parsers.StoreTrueFalseAction,
        help=(
            'Enable machine learning engine to dynamically detect malicious PE'
            ' files.'
        ),
    )
    parser.add_argument(
        '--analyze-powershell-script-1',
        action=arg_parsers.StoreTrueFalseAction,
        help=(
            'Enable machine learning engine to dynamically identify malicious'
            ' PowerShell scripts with known length.'
        ),
    )
    parser.add_argument(
        '--analyze-powershell-script-2',
        action=arg_parsers.StoreTrueFalseAction,
        help=(
            'Enable machine learning engine to dynamically identify malicious'
            ' PowerShell script without known length.'
        ),
    )
    parser.add_argument(
        '--analyze-elf',
        action=arg_parsers.StoreTrueFalseAction,
        help=(
            'Enable machine learning engine to dynamically detect malicious ELF'
            ' files.'
        ),
    )
    parser.add_argument(
        '--analyze-ms-office',
        action=arg_parsers.StoreTrueFalseAction,
        help=(
            'Enable machine learning engine to dynamically detect malicious'
            ' MSOffice (97-03) files.'
        ),
    )
    parser.add_argument(
        '--analyze-shell',
        action=arg_parsers.StoreTrueFalseAction,
        help=(
            'Enable machine learning engine to dynamically detect malicious'
            ' Shell files.'
        ),
    )
    parser.add_argument(
        '--analyze-ooxml',
        action=arg_parsers.StoreTrueFalseAction,
        help=(
            'Enable machine learning engine to dynamically detect malicious'
            ' OOXML files.'
        ),
    )
    parser.add_argument(
        '--analyze-macho',
        action=arg_parsers.StoreTrueFalseAction,
        help=(
            'Enable machine learning engine to dynamically detect malicious'
            ' Mach-O files.'
        ),
    )

  def Run(self, args):
    client = wildfire_api.Client(self.ReleaseTrack())
    security_profile = args.CONCEPTS.security_profile.Parse()
    is_async = args.async_

    if args.location != 'global':
      raise core_exceptions.Error(
          'Only `global` location is supported, but got: %s' % args.location
      )

    kwargs = {}
    update_fields = [
        'description',
        'wildfire_realtime_lookup',
        'analyze_windows_executables',
        'analyze_powershell_script_1',
        'analyze_powershell_script_2',
        'analyze_elf',
        'analyze_ms_office',
        'analyze_shell',
        'analyze_ooxml',
        'analyze_macho',
    ]
    # If --field is used, args.IsSpecified(field) is true,
    # and getattr(args, field) returns True.
    # If --no-field is used, args.IsSpecified(field) is true,
    # and getattr(args, field) returns False.
    # If neither is used, args.IsSpecified(field) is false,
    # and the field is not added to kwargs.
    # Therefore, kwargs only contains fields that the user explicitly wants to
    # change.
    for field in update_fields:
      if args.IsSpecified(field):
        kwargs[field] = getattr(args, field)

    response = client.UpdateWildfireAnalysisProfile(
        name=security_profile.result.RelativeName(),
        **kwargs,
    )

    if is_async:
      operation_id = response.name
      log.status.Print(
          'Check for operation completion status using operation ID:',
          operation_id,
      )
      return response

    return client.WaitForOperation(
        operation_ref=client.GetOperationsRef(response),
        message='Waiting for security-profile [{}] to be updated'.format(
            security_profile.result.RelativeName()
        ),
        has_result=True,
    )
