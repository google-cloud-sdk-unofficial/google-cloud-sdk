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
"""Command for testing IAM permissions on target TCP proxies."""

from typing import Any, ClassVar

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_tcp_proxies import flags


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.PREVIEW)
class TestIamPermissions(base.Command):
  """Test IAM permissions for a target TCP proxy."""

  TARGET_TCP_PROXY_ARG: ClassVar[Any] = None

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor) -> None:
    """Specifies the arguments for the command.

    Args:
      parser: The command-line parser to register arguments.
    """
    cls.TARGET_TCP_PROXY_ARG = flags.TargetTcpProxyArgument(
        allow_regional=False
    )
    cls.TARGET_TCP_PROXY_ARG.AddArgument(
        parser, operation_type='test IAM permissions for'
    )
    parser.add_argument(
        '--permissions',
        metavar='PERMISSION',
        type=arg_parsers.ArgList(),
        required=True,
        help='Set of permissions to check for the resource.',
    )

  def Run(self, args: parser_extensions.Namespace) -> Any:
    """Runs the command.

    Args:
      args: The argparse namespace containing the arguments.

    Returns:
      The response message from the testIamPermissions API.
    """
    return self._Run(args, allow_regional=False)

  def _Run(
      self, args: parser_extensions.Namespace, allow_regional: bool
  ) -> Any:
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    apitools_client = client.apitools_client
    messages = client.messages

    ref = self.TARGET_TCP_PROXY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL
    )

    test_permissions_request = messages.TestPermissionsRequest(
        permissions=args.permissions
    )

    if ref.Collection() == 'compute.targetTcpProxies':
      service = apitools_client.targetTcpProxies
      request = messages.ComputeTargetTcpProxiesTestIamPermissionsRequest(
          resource=ref.Name(),
          project=ref.project,
          testPermissionsRequest=test_permissions_request,
      )
    elif ref.Collection() == 'compute.regionTargetTcpProxies':
      if not allow_regional:
        raise ValueError(
            'Regional target TCP proxies not supported for this track.'
        )
      service = apitools_client.regionTargetTcpProxies
      request = messages.ComputeRegionTargetTcpProxiesTestIamPermissionsRequest(
          resource=ref.Name(),
          region=ref.region,
          project=ref.project,
          testPermissionsRequest=test_permissions_request,
      )
    else:
      raise ValueError('Unknown reference type {0}'.format(ref.Collection()))

    errors = []
    resources = client.MakeRequests(
        [(service, 'TestIamPermissions', request)], errors
    )
    if errors:
      utils.RaiseToolException(errors)
    return resources[0]


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class TestIamPermissionsAlphaBeta(TestIamPermissions):
  """Test IAM permissions for a target TCP proxy."""

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor) -> None:
    """Specifies the arguments for the command.

    Args:
      parser: The command-line parser to register arguments.
    """
    cls.TARGET_TCP_PROXY_ARG = flags.TargetTcpProxyArgument(allow_regional=True)
    cls.TARGET_TCP_PROXY_ARG.AddArgument(
        parser, operation_type='test IAM permissions for'
    )
    parser.add_argument(
        '--permissions',
        metavar='PERMISSION',
        type=arg_parsers.ArgList(),
        required=True,
        help='Set of permissions to check for the resource.',
    )

  def Run(self, args: parser_extensions.Namespace) -> Any:
    """Runs the command.

    Args:
      args: The argparse namespace containing the arguments.

    Returns:
      The response message from the testIamPermissions API.
    """
    return self._Run(args, allow_regional=True)


_COMMON_DESCRIPTION = """\
    *{command}* tests the IAM permissions that a caller has on a
    target TCP proxy.

    Note: This operation is designed to be used for building
    permission-aware UIs and command-line tools, not for authorization
    checking. This operation may "fail open" without warning.
    """

TestIamPermissions.detailed_help = {
    'brief': 'Test IAM permissions for a target TCP proxy',
    'DESCRIPTION': _COMMON_DESCRIPTION,
    'EXAMPLES': (
        """\
        To test if the caller has 'compute.targetTcpProxies.get' permission on a
        global target TCP proxy 'my-proxy', run:

          $ {command} my-proxy --permissions=compute.targetTcpProxies.get
        """
    ),
}

TestIamPermissionsAlphaBeta.detailed_help = {
    'brief': 'Test IAM permissions for a target TCP proxy',
    'DESCRIPTION': _COMMON_DESCRIPTION,
    'EXAMPLES': (
        """\
        To test if the caller has 'compute.targetTcpProxies.get' permission on a
        global target TCP proxy 'my-proxy', run:

          $ {command} my-proxy --permissions=compute.targetTcpProxies.get

        To test permissions on a regional target TCP proxy 'my-regional-proxy' in
        region 'us-central1', run:

          $ {command} my-regional-proxy --region=us-central1 --permissions=compute.targetTcpProxies.get
        """
    ),
}
