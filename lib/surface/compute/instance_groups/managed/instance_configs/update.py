# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Command for deleting managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update per instance config of a managed instance group.

  *{command}* updates per instance config of a Google Compute Engine managed
  instance group.
  """

  @staticmethod
  def Args(parser):
    instance_groups_flags.GetInstanceGroupManagerArg(
        region_flag=False).AddArgument(parser, operation_type='update')
    parser.add_argument(
        '--instance',
    )
    instance_groups_flags.AddSettingStatefulDisksFlag(parser, required=True)

  def _GetInstance(self, holder, igm_ref, instance_name):
    messages = holder.client.messages
    instance_ref = holder.resources.Parse(
        instance_name,
        collection='compute.instances',
        params={
            'project': igm_ref.project,
            'zone': igm_ref.zone,
        })
    request = messages.ComputeInstancesGetRequest(
        instance=instance_ref.Name(),
        project=instance_ref.project,
        zone=instance_ref.zone,
    )
    return holder.client.apitools_client.instances.Get(request)

  def _GetDiskSource(self, instance, device):
    for d in instance.disks:
      if d.deviceName == device:
        return d.source
    raise exceptions.BadArgumentException(
        '--stateful-disks',
        'The instance doesn\'t have a disk with specified device name.')

  def _GetDiskOverride(self, messages, device, instance):
    return messages.ManagedInstanceOverrideDiskOverride(
        deviceName=device,
        source=self._GetDiskSource(instance, device)
    )

  def _GetUpdatePerInstanceConfigRequests(
      self, client, igm_ref, instance, stateful_devices):
    """Returns a list of delete messages for instance group managers."""

    if not stateful_devices:
      stateful_devices = []

    messages = client.messages
    disk_overrides = [
        self._GetDiskOverride(messages, device, instance)
        for device in stateful_devices
    ]
    override = messages.ManagedInstanceOverride(disks=disk_overrides)
    per_instance_config = messages.PerInstanceConfig(
        instance=instance.selfLink,
        override=override,
    )
    req = messages.InstanceGroupManagersUpdatePerInstanceConfigsReq(
        perInstanceConfigs=[per_instance_config],
    )
    return messages.ComputeInstanceGroupManagersUpdatePerInstanceConfigsRequest(
        instanceGroupManager=igm_ref.Name(),
        instanceGroupManagersUpdatePerInstanceConfigsReq=req,
        project=igm_ref.project,
        zone=igm_ref.zone,
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    project = properties.VALUES.core.project.Get(required=True)
    igm_ref = (
        instance_groups_flags.GetInstanceGroupManagerArg(
            region_flag=False).
        ResolveAsResource)(
            args, holder.resources, default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=flags.GetDefaultScopeLister(client, project))

    instance = self._GetInstance(holder, igm_ref, args.instance)
    request = self._GetUpdatePerInstanceConfigRequests(
        client, igm_ref, instance, args.stateful_disks)

    service = client.apitools_client.instanceGroupManagers
    operation = service.UpdatePerInstanceConfigs(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')
    operation_poller = poller.Poller(service)
    return waiter.WaitFor(
        operation_poller, operation_ref, 'Updating instance configs.')
