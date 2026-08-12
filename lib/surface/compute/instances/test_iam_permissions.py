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
"""Command for testing IAM permissions for an instance."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.GA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.PREVIEW,
)
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine instance."""

  detailed_help = {
      'brief': 'Test IAM permissions for a Compute Engine instance.',
      'DESCRIPTION': (
          """\
          ``{command}'' tests IAM permissions for a Compute Engine instance.
          """
      ),
      'EXAMPLES': (
          """\
          To test if the caller has `compute.instances.get` permission on `instance-1`:

            $ {command} instance-1 --permissions=compute.instances.get
          """
      ),
  }

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument(
        '--permissions',
        type=str,
        required=True,
        help="""\
        Single IAM permission to test.
        """,
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client),
    )

    messages = client.messages
    request = messages.ComputeInstancesTestIamPermissionsRequest(
        project=instance_ref.project,
        zone=instance_ref.zone,
        resource=instance_ref.instance,
        testPermissionsRequest=messages.TestPermissionsRequest(
            permissions=[args.permissions]
        ),
    )

    return client.MakeRequests(
        [(client.apitools_client.instances, 'TestIamPermissions', request)]
    )[0]
