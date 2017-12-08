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
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instance_groups import flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetNamedPorts(base_classes.NoOutputAsyncMutator):
  """Sets named ports for instance groups."""

  @property
  def service(self):
    return self.compute.instanceGroups

  @property
  def method(self):
    return 'SetNamedPorts'

  @property
  def resource_type(self):
    return 'instanceGroups'

  @staticmethod
  def Args(parser):
    flags.AddNamedPortsArgs(parser)
    flags.AddScopeArgs(parser=parser, multizonal=False)

  def CreateRequests(self, args):
    group_ref = self.CreateZonalReference(args.group, args.zone)
    ports = instance_groups_utils.ValidateAndParseNamedPortsArgs(
        self.messages, args.named_ports)
    # service should be always zonal
    request, _ = instance_groups_utils.GetSetNamedPortsRequestForGroup(
        self.compute_client, group_ref, ports)
    return [(self.service, self.method, request)]

  detailed_help = instance_groups_utils.SET_NAMED_PORTS_HELP


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
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
    flags.AddNamedPortsArgs(parser)
    flags.AddScopeArgs(parser=parser, multizonal=True)

  def CreateRequests(self, args):
    group_ref = instance_groups_utils.CreateInstanceGroupReference(
        scope_prompter=self, compute=self.compute, resources=self.resources,
        name=args.group, region=args.region, zone=args.zone,
        zonal_resource_type='instanceGroups',
        regional_resource_type='regionInstanceGroups')
    ports = instance_groups_utils.ValidateAndParseNamedPortsArgs(
        self.messages, args.named_ports)
    # service could be zonal or regional
    request, service = instance_groups_utils.GetSetNamedPortsRequestForGroup(
        self.compute_client, group_ref, ports)
    return [(service, self.method, request)]

  detailed_help = instance_groups_utils.SET_NAMED_PORTS_HELP
