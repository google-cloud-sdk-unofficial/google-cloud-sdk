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
"""Command for testing IAM permissions on managed instance groups."""

from typing import Any

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine managed instance group."""

  detailed_help = {
      'brief': (
          'Test IAM permissions for a Compute Engine managed instance group.'
      ),
      'DESCRIPTION': (
          """\
          *{command}* tests the IAM permissions that a caller has on a
          Compute Engine managed instance group.

          Note: This operation is designed to be used for building
          permission-aware UIs and command-line tools, not for authorization
          checking. This operation may "fail open" without warning.
          """
      ),
      'EXAMPLES': (
          """\
          To test if the caller has `compute.instanceGroupManagers.get` and
          `compute.instanceGroupManagers.update` permissions on a zonal managed
          instance group `my-mig` in zone `us-central1-a`, run:

            $ {command} my-mig --zone=us-central1-a \\
                --permissions=compute.instanceGroupManagers.get,compute.instanceGroupManagers.update

          To test permissions on a regional managed instance group `my-rmig` in region `us-central1`, run:

            $ {command} my-rmig --region=us-central1 \\
                --permissions=compute.instanceGroupManagers.get,compute.instanceGroupManagers.update
          """
      ),
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
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

    ref = instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    test_permissions_request = messages.TestPermissionsRequest(
        permissions=args.permissions
    )

    if ref.Collection() == 'compute.instanceGroupManagers':
      service = apitools_client.instanceGroupManagers
      request = messages.ComputeInstanceGroupManagersTestIamPermissionsRequest(
          resource=ref.Name(),
          zone=ref.zone,
          project=ref.project,
          testPermissionsRequest=test_permissions_request,
      )
    elif ref.Collection() == 'compute.regionInstanceGroupManagers':
      service = apitools_client.regionInstanceGroupManagers
      request = (
          messages.ComputeRegionInstanceGroupManagersTestIamPermissionsRequest(
              resource=ref.Name(),
              region=ref.region,
              project=ref.project,
              testPermissionsRequest=test_permissions_request,
          )
      )
    else:
      raise ValueError('Unknown reference type {0}'.format(ref.Collection()))

    return client.MakeRequests([(service, 'TestIamPermissions', request)])[0]
