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

"""Command for setting machine type for virtual machine instances."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


def _CommonArgs(parser, release_track):
  """Register parser args common to all tracks."""
  instance_flags.INSTANCE_ARG.AddArgument(parser)
  instance_flags.AddMachineTypeArgs(parser)
  instance_flags.AddCustomMachineTypeArgs(parser)
  if release_track in [base.ReleaseTrack.ALPHA]:
    instance_flags.AddExtendedMachineTypeArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class SetMachineType(base_classes.NoOutputAsyncMutator):
  """Set machine type for Google Compute Engine virtual machine instances."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, release_track=base.ReleaseTrack.GA)

  @property
  def service(self):
    return self.compute.instances

  @property
  def method(self):
    return 'SetMachineType'

  @property
  def resource_type(self):
    return 'instances'

  def CreateRequests(self, args):
    """Returns a list of request necessary for setting scheduling options."""
    instance_ref = instance_flags.INSTANCE_ARG.ResolveAsResource(
        args, self.resources, scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))

    machine_type = instance_utils.InterpretMachineType(
        machine_type=args.machine_type,
        custom_cpu=args.custom_cpu,
        custom_memory=args.custom_memory,
        ext=getattr(args, 'custom_extensions', None))

    instance_utils.CheckCustomCpuRamRatio(
        self.compute_client, self.project, instance_ref.zone, machine_type)

    machine_type_uri = self.resources.Parse(
        machine_type, collection='compute.machineTypes',
        params={'zone': instance_ref.zone}).SelfLink()

    set_machine_type_request = self.messages.InstancesSetMachineTypeRequest(
        machineType=machine_type_uri)
    request = self.messages.ComputeInstancesSetMachineTypeRequest(
        instance=instance_ref.Name(),
        project=self.project,
        instancesSetMachineTypeRequest=set_machine_type_request,
        zone=instance_ref.zone)

    return (request,)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetMachineTypeAlpha(SetMachineType):
  """Set machine type for Google Compute Engine virtual machine instances."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser, release_track=base.ReleaseTrack.ALPHA)


SetMachineType.detailed_help = {
    'brief': 'Set machine type for Google Compute Engine virtual machines',
    'DESCRIPTION': """\
        ``{command}'' allows you to change the machine type of a virtual machine
        in the *TERMINATED* state (that is, a virtual machine instance that
        has been stopped).

        For example, if ``example-instance'' is a ``g1-small'' virtual machine
        currently in the *TERMINATED* state, running:

          $ {command} example-instance --zone us-central1-b --machine-type n1-standard-4

        will change the machine type to ``n1-standard-4'', so that when you
        next start ``example-instance'', it will be provisioned as an
        ``n1-standard-4'' instead of a ``g1-small''.

        See [](https://cloud.google.com/compute/docs/machine-types) for more
        information on machine types.
        """,
}
