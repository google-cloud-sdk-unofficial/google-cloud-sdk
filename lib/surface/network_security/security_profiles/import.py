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
"""Import Security Profile."""


from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.network_security.security_profiles import sp_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.export import util
from googlecloudsdk.command_lib.network_security import sp_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'DESCRIPTION': """

          Import a Security Profile.

        """,
    'EXAMPLES': """
          To import a Security Profile from a YAML file, run:

              $ {command} my-security-profile --organization=1234 --location=global --source=my-security-profile.yaml

        """,
}

_PROJECT_SCOPE_SUPPORTED_TRACKS = (
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
)


def _HandleOperation(operation, is_async, client, return_final_operation):
  # Return the in-progress operation if async is requested.
  if is_async:
    log.status.Print(
        'Check for operation completion status using operation ID:',
        operation.name,
    )
    return operation

  # Default operation poller if async is not specified.
  return client.WaitForOperation(
      operation_ref=client.GetOperationsRef(operation),
      message='Waiting for operation [{}] to complete'.format(
          operation.name
      ),
      has_result=True,
      return_final_operation=return_final_operation,
  )


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Import(base.ImportCommand):
  """Import Security Profile."""

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
    util.AddImportFlags(
        parser, sp_api.GetSchemaPath(cls.ReleaseTrack(), for_help=True))

  def Run(self, args):
    result = args.CONCEPTS.security_profile.Parse()
    security_profile = result.result
    is_async = args.async_

    project_scoped = (
        result.concept_type.name
        == sp_flags.PROJECT_SECURITY_PROFILE_RESOURCE_COLLECTION
    )
    client = sp_api.Client(self.ReleaseTrack(), project_scoped)

    data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)
    sp_yaml = yaml.load(data)
    sp = util.Import(
        message_type=client.messages.SecurityProfile,
        stream=yaml.dump(sp_yaml),
    )

    try:
      client.GetSecurityProfile(security_profile.RelativeName())
    except apitools_exceptions.HttpError as error:
      if error.status_code != 404:
        raise error
      # Security Profile does not exist, create a new one.
      op = client.CreateSecurityProfile(
          parent=security_profile.Parent().RelativeName(),
          sp_id=security_profile.Name(),
          sp=sp,
      )
      return _HandleOperation(
          op, is_async, client, return_final_operation=False
      )

    # Security Profile exists, update it.
    op = client.FullUpdateSecurityProfile(
        name=security_profile.RelativeName(),
        sp=sp,
    )
    return _HandleOperation(op, is_async, client, return_final_operation=True)
