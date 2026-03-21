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

"""Command to describe snapshot recycle bin policy."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Describe the project's or organization's snapshot recycle bin policy."""

  detailed_help = {
      'EXAMPLES': """
      To describe the snapshot recycle bin policy for project `my-project`:

        $ {command} --project=my-project

      To describe the snapshot recycle bin policy for organization `123456789`:

        $ {command} --organization=123456789
      """,
  }

  @classmethod
  def Args(cls, parser):
    project_or_organization = parser.add_mutually_exclusive_group()
    project_or_organization.add_argument(
        '--organization',
        help='Organization ID for the policy.',
    )
    project_or_organization.add_argument(
        '--project',
        help='Project ID for the policy.',
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    if args.organization:
      request = messages.ComputeOrganizationSnapshotRecycleBinPolicyGetRequest(
          organization='organizations/' + args.organization
      )
      service = client.apitools_client.organizationSnapshotRecycleBinPolicy
    else:
      project = args.project or properties.VALUES.core.project.Get(
          required=True
      )
      request = messages.ComputeSnapshotRecycleBinPolicyGetRequest(
          project=project
      )
      service = client.apitools_client.snapshotRecycleBinPolicy

    return client.MakeRequests([(service, 'Get', request)])[0]
