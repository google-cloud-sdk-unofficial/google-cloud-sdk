# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Command for setting named ports in instance groups."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags


class SetNamedPortsAlpha(base_classes.NoOutputAsyncMutator):
  """Sets named ports for instance groups."""

  @property
  def service(self):
    # service property not implemented on this command as it is specified
    # for each request
    return None

  @property
  def method(self):
    return 'SetNamedPorts'

  @staticmethod
  def Args(parser):
    flags.MULTISCOPE_INSTANCE_GROUP_ARG.AddArgument(parser)
    flags.AddNamedPortsArgs(parser)

  def CreateRequests(self, args):
    group_ref = flags.MULTISCOPE_INSTANCE_GROUP_ARG.ResolveAsResource(
        args, self.resources, default_scope=compute_scope.ScopeEnum.ZONE,
        scope_lister=compute_flags.GetDefaultScopeLister(
            self.compute_client, self.project))
    ports = instance_groups_utils.ValidateAndParseNamedPortsArgs(
        self.messages, args.named_ports)
    # service could be zonal or regional
    request, service = instance_groups_utils.GetSetNamedPortsRequestForGroup(
        self.compute_client, group_ref, ports)
    return [(service, self.method, request)]

  detailed_help = instance_groups_utils.SET_NAMED_PORTS_HELP
