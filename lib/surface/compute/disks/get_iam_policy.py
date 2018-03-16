# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Command to get IAM policy for a resource."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetIamPolicy(base.ListCommand):
  """Get the IAM Policy for a Google Compute Engine disk.

  *{command}* displays the IAM Policy associated with a Google Compute Engine
  disk in a project.
  """

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)  # doesn't do anything in this case
    GetIamPolicy.disk_arg = disks_flags.MakeDiskArg(plural=False)
    GetIamPolicy.disk_arg.AddArgument(parser,
                                      operation_type='get the IAM policy of')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    disk_ref = GetIamPolicy.disk_arg.ResolveAsResource(args, holder.resources)
    request = client.messages.ComputeDisksGetIamPolicyRequest(
        resource=disk_ref.disk, zone=disk_ref.zone, project=disk_ref.project)
    return client.apitools_client.disks.GetIamPolicy(request)
