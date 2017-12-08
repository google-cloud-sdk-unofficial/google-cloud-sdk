# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command for suspending an instance."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Suspend(base_classes.NoOutputAsyncMutator):
  """Suspend a virtual machine instance.

  *{command}* is used to suspend a running Google Compute Engine virtual
  machine. Only a running virtual machine can be suspended.
  """

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCES_ARG.AddArgument(parser)
    parser.add_argument(
        '--discard-local-ssd',
        action='store_true',
        help=('If provided, local SSD data is discarded.'))
    # TODO(user): consider adding detailed help.

  @property
  def service(self):
    return self.compute.instances

  @property
  def method(self):
    return 'Suspend'

  @property
  def resource_type(self):
    return 'instances'

  def _CreateSuspendRequest(self, instance_ref, discard_local_ssd):
    return self.messages.ComputeInstancesSuspendRequest(
        discardLocalSsd=discard_local_ssd,
        instance=instance_ref.Name(),
        project=self.project,
        zone=instance_ref.zone)

  def CreateRequests(self, args):
    instance_refs = instance_flags.INSTANCES_ARG.ResolveAsResource(
        args, self.resources, scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))
    return [self._CreateSuspendRequest(instance_ref, args.discard_local_ssd)
            for instance_ref in instance_refs]


Suspend.detailed_help = {
    'brief': 'Suspend a virtual machine instance',
    'DESCRIPTION': """\
        *{command}* is used to suspend a Google Compute Engine virtual machine.
        Suspending a VM is the equivalent of sleep or standby mode:
        the guest receives an ACPI S3 suspend signal, after which all VM state
        is saved to temporary storage.  An instance can only be suspended while
        it is in the RUNNING state.  A suspended instance will be put in
        SUSPENDED state.

        Alpha restrictions: Suspending a Preemptible VM is not supported and
        will result in an API error. Suspending a VM that is using CSEK or GPUs
        is not supported and will result in an API error.
        """,
}
