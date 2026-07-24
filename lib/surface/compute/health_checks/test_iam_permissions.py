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
"""Command for testing IAM permissions on health checks."""

from typing import Any

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import health_checks_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.health_checks import flags


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA,
    base.ReleaseTrack.PREVIEW,
)
@base.UniverseCompatible
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine health check."""

  detailed_help = {
      'brief': 'Test IAM permissions for a Compute Engine health check.',
      'DESCRIPTION': (
          """\
          *{command}* tests the IAM permissions that a caller has on a
          Compute Engine health check.

          Note: This operation is designed to be used for building
          permission-aware UIs and command-line tools, not for authorization
          checking. This operation may "fail open" without warning.
          """
      ),
      'EXAMPLES': (
          """\
          To test if the caller has `compute.healthChecks.getIamPolicy` permission on a health check `my-health-check`, run:

            $ {command} my-health-check --permissions=compute.healthChecks.getIamPolicy
          """
      ),
  }

  HEALTH_CHECK_ARG = None

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor) -> None:
    cls.HEALTH_CHECK_ARG = flags.HealthCheckArgument('')
    cls.HEALTH_CHECK_ARG.AddArgument(
        parser, operation_type='test IAM permissions for'
    )
    parser.add_argument(
        '--permissions',
        metavar='PERMISSION',
        type=arg_parsers.ArgList(),
        required=True,
        help='The set of permissions to check for the resource.',
    )

  def Run(self, args: parser_extensions.Namespace) -> Any:
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    apitools_client = client.apitools_client
    messages = client.messages
    resources = holder.resources

    ref = self.HEALTH_CHECK_ARG.ResolveAsResource(
        args,
        resources,
        default_scope=compute_scope.ScopeEnum.GLOBAL,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    test_permissions_request = messages.TestPermissionsRequest(
        permissions=args.permissions
    )

    if health_checks_utils.IsRegionalHealthCheckRef(ref):
      service = apitools_client.regionHealthChecks
      request = messages.ComputeRegionHealthChecksTestIamPermissionsRequest(
          resource=ref.Name(),
          region=ref.region,
          project=ref.project,
          testPermissionsRequest=test_permissions_request,
      )
    else:
      service = apitools_client.healthChecks
      request = messages.ComputeHealthChecksTestIamPermissionsRequest(
          resource=ref.Name(),
          project=ref.project,
          testPermissionsRequest=test_permissions_request,
      )

    return client.MakeRequests([(service, 'TestIamPermissions', request)])[0]
