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
"""Command to get the VM extension state."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instances import flags


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetVmExtensionState(base.DescribeCommand):
  """Get the VM Extension State for a compute instance."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Get the VM Extension State for a compute instance.
          """,
      'EXAMPLES':
          """\
          To get the VM extension state for instance 'my-instance' in zone 'ZONE' for
          extension 'my-extension', run:

            $ {command} my-instance --extension-name=my-extension --zone=ZONE
          """
  }

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(
        parser, operation_type='get the VM Extension State for')
    flags.AddExtensionNameArg(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    request = (
        client.apitools_client.instances, 'GetVmExtensionState',
        client.messages.ComputeInstancesGetVmExtensionStateRequest(
            instance=instance_ref.instance,
            zone=instance_ref.zone,
            project=instance_ref.project,
            extensionName=args.extension_name))

    errors = []
    objects = client.MakeRequests(requests=[request], errors_to_collect=errors)
    if errors:
      utils.RaiseToolException(
          errors, error_message='Could not get VM Extension State:')
    response = objects[0]
    return response
