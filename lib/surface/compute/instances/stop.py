# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Command for stopping an instance."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Stop(base_classes.NoOutputAsyncMutator):
  """Stop a virtual machine instance."""

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCES_ARG.AddArgument(parser)
    parser.add_argument(
        '--discard-local-ssd',
        action='store_true',
        help=('If provided, local SSD data is discarded.'))

  @property
  def service(self):
    return self.compute.instances

  @property
  def method(self):
    return 'Stop'

  @property
  def resource_type(self):
    return 'instances'

  def _CreateStopRequest(self, instance_ref, unused_discard_local_ssd):
    return self.messages.ComputeInstancesStopRequest(
        instance=instance_ref.Name(),
        project=self.project,
        zone=instance_ref.zone)

  def CreateRequests(self, args):
    instance_refs = instance_flags.INSTANCES_ARG.ResolveAsResource(
        args, self.resources, scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))
    return [self._CreateStopRequest(instance_ref, args.discard_local_ssd)
            for instance_ref in instance_refs]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class StopAlpha(Stop, base_classes.BaseCommand):

  def _CreateStopRequest(self, instance_ref, discard_local_ssd):
    """Adds the discardLocalSsd var into the message."""
    return self.messages.ComputeInstancesStopRequest(
        discardLocalSsd=discard_local_ssd,
        instance=instance_ref.Name(),
        project=self.project,
        zone=instance_ref.zone)


Stop.detailed_help = {
    'brief': 'Stop a virtual machine instance',
    'DESCRIPTION': """\
        *{command}* is used stop a Google Compute Engine virtual machine.
        Stopping a VM performs a clean shutdown, much like invoking the shutdown
        functionality of a workstation or laptop. Stopping a VM with a local SSD
        is not supported and will result in an API error.
        """,
}
