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
"""Command for labels update to instances."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.util import labels_util

DETAILED_HELP = {
    'DESCRIPTION': """\
        *{command}* updates labels and requested CPU Platform for a Google
        Compute
        Engine virtual machine.  For example:

          $ {command} example-instance --zone us-central1-a --update-labels=k0=value1,k1=value2 --remove-labels=k3

        will add/update labels ``k0'' and ``k1'' and remove labels with key
        ``k3''.

        Labels can be used to identify the instance and to filter them as in

          $ {parent_command} list --filter='labels.k1:value2'

        To list existing labels

          $ {parent_command} describe example-instance --format='default(labels)'
  """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Google Compute Engine virtual machine."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser, operation_type='update')
    labels_util.AddUpdateLabelsFlags(parser)
    flags.AddMinCpuPlatformArgs(parser, Update.ReleaseTrack())
    flags.AddDeletionProtectionFlag(parser, use_default_value=False)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(holder.client))

    result = None

    labels_operation_ref = None
    min_cpu_platform_operation_ref = None
    deletion_protection_operation_ref = None

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      instance = client.instances.Get(
          messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))
      result = instance
      labels_operation_ref = self._GetLabelsOperationRef(
          labels_diff, instance, instance_ref, holder)
    if hasattr(args, 'min_cpu_platform') and args.min_cpu_platform is not None:
      min_cpu_platform_operation_ref = self._GetMinCpuPlatformOperationRef(
          args.min_cpu_platform, instance_ref, holder)
    if args.deletion_protection is not None:
      deletion_protection_operation_ref = (
          self._GetDeletionProtectionOperationRef(
              args.deletion_protection, instance_ref, holder))

    operation_poller = poller.Poller(client.instances)
    result = self._WaitForResult(
        operation_poller, labels_operation_ref,
        'Updating labels of instance [{0}]', instance_ref.Name()) or result
    result = self._WaitForResult(
        operation_poller, min_cpu_platform_operation_ref,
        'Changing minimum CPU platform of instance [{0}]',
        instance_ref.Name()) or result
    result = self._WaitForResult(
        operation_poller, deletion_protection_operation_ref,
        'Setting deletion protection of instance [{0}] to [{1}]',
        instance_ref.Name(), args.deletion_protection) or result
    return result

  def _GetLabelsOperationRef(self, labels_diff, instance, instance_ref, holder):
    client = holder.client.apitools_client
    messages = holder.client.messages

    replacement = labels_diff.Apply(
        messages.InstancesSetLabelsRequest.LabelsValue,
        instance.labels)

    if replacement:
      request = messages.ComputeInstancesSetLabelsRequest(
          project=instance_ref.project,
          instance=instance_ref.instance,
          zone=instance_ref.zone,
          instancesSetLabelsRequest=
          messages.InstancesSetLabelsRequest(
              labelFingerprint=instance.labelFingerprint,
              labels=replacement))

      operation = client.instances.SetLabels(request)
      return holder.resources.Parse(
          operation.selfLink, collection='compute.zoneOperations')

  def _GetMinCpuPlatformOperationRef(self, min_cpu_platform, instance_ref,
                                     holder):
    client = holder.client.apitools_client
    messages = holder.client.messages
    embedded_request = messages.InstancesSetMinCpuPlatformRequest(
        minCpuPlatform=min_cpu_platform or None)
    request = messages.ComputeInstancesSetMinCpuPlatformRequest(
        instance=instance_ref.instance,
        project=instance_ref.project,
        instancesSetMinCpuPlatformRequest=embedded_request,
        zone=instance_ref.zone)

    operation = client.instances.SetMinCpuPlatform(request)
    return holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')

  def _GetDeletionProtectionOperationRef(self, deletion_protection,
                                         instance_ref, holder):
    client = holder.client.apitools_client
    messages = holder.client.messages
    request = messages.ComputeInstancesSetDeletionProtectionRequest(
        deletionProtection=deletion_protection,
        project=instance_ref.project,
        resource=instance_ref.instance,
        zone=instance_ref.zone)

    operation = client.instances.SetDeletionProtection(request)
    return holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')

  def _WaitForResult(self, operation_poller, operation_ref, message, *args):
    if operation_ref:
      return waiter.WaitFor(
          operation_poller, operation_ref, message.format(*args))
    return None


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a Google Compute Engine virtual machine."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser, operation_type='update')
    labels_util.AddUpdateLabelsFlags(parser)
    flags.AddMinCpuPlatformArgs(parser, UpdateBeta.ReleaseTrack())
    flags.AddDeletionProtectionFlag(parser, use_default_value=False)


Update.detailed_help = DETAILED_HELP
