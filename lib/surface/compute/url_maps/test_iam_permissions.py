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
"""Command for testing IAM permissions on URL maps."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.url_maps import flags


@base.ReleaseTracks(
    base.ReleaseTrack.GA,
    base.ReleaseTrack.PREVIEW,
)
@base.UniverseCompatible
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine URL map."""

  detailed_help = {
      'brief': 'Test IAM permissions for a Compute Engine URL map.',
      'DESCRIPTION': (
          """\
          *{command}* tests the IAM permissions that a caller has on a
          Compute Engine URL map.
          """
      ),
      'EXAMPLES': (
          """\
          To test if the caller has `compute.urlMaps.get` and
          `compute.urlMaps.update` permissions on a global URL map `my-map`, run:

            $ {command} my-map \\
                --permissions=compute.urlMaps.get,compute.urlMaps.update
          """
      ),
  }

  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.URL_MAP_ARG = flags.GlobalUrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(
        parser, operation_type='test IAM permissions for'
    )
    parser.add_argument(
        '--permissions',
        metavar='PERMISSION',
        type=arg_parsers.ArgList(),
        required=True,
        help='The set of permissions to check for the resource.',
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages
    resources = holder.resources

    ref = self.URL_MAP_ARG.ResolveAsResource(
        args,
        resources,
        default_scope=compute_scope.ScopeEnum.GLOBAL,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    test_permissions_request = messages.TestPermissionsRequest(
        permissions=args.permissions
    )

    if ref.Collection() == 'compute.regionUrlMaps':
      raise exceptions.InvalidArgumentException(
          '--region',
          'Regional URL maps do not support testing IAM permissions in this'
          ' release track.',
      )
    service = client.apitools_client.urlMaps
    request = messages.ComputeUrlMapsTestIamPermissionsRequest(
        resource=ref.Name(),
        project=ref.project,
        testPermissionsRequest=test_permissions_request,
    )

    return client.MakeRequests([(service, 'TestIamPermissions', request)])[0]


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
)
class TestIamPermissionsAlphaBeta(TestIamPermissions):

  """Test IAM permissions for a Compute Engine URL map."""

  detailed_help = {
      'brief': 'Test IAM permissions for a Compute Engine URL map.',
      'DESCRIPTION': (
          """\
          *{command}* tests the IAM permissions that a caller has on a
          Compute Engine URL map.
          """
      ),
      'EXAMPLES': (
          """\
          To test if the caller has `compute.urlMaps.get` and
          `compute.urlMaps.update` permissions on a global URL map `my-map`, run:

            $ {command} my-map \\
                --permissions=compute.urlMaps.get,compute.urlMaps.update

          To test permissions on a regional URL map `my-regional-map` in region `us-central1`, run:

            $ {command} my-regional-map --region=us-central1 \\
                --permissions=compute.urlMaps.get,compute.urlMaps.update
          """
      ),
  }

  @classmethod
  def Args(cls, parser):
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(
        parser, operation_type='test IAM permissions for'
    )
    parser.add_argument(
        '--permissions',
        metavar='PERMISSION',
        type=arg_parsers.ArgList(),
        required=True,
        help='The set of permissions to check for the resource.',
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages
    resources = holder.resources

    ref = self.URL_MAP_ARG.ResolveAsResource(
        args,
        resources,
        default_scope=compute_scope.ScopeEnum.GLOBAL,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    test_permissions_request = messages.TestPermissionsRequest(
        permissions=args.permissions
    )

    if ref.Collection() == 'compute.regionUrlMaps':
      service = client.apitools_client.regionUrlMaps
      request = messages.ComputeRegionUrlMapsTestIamPermissionsRequest(
          resource=ref.Name(),
          region=ref.region,
          project=ref.project,
          testPermissionsRequest=test_permissions_request,
      )
    else:
      service = client.apitools_client.urlMaps
      request = messages.ComputeUrlMapsTestIamPermissionsRequest(
          resource=ref.Name(),
          project=ref.project,
          testPermissionsRequest=test_permissions_request,
      )

    return client.MakeRequests([(service, 'TestIamPermissions', request)])[0]
