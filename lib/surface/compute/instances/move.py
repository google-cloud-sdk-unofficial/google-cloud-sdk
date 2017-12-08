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
"""Command for moving instances."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.projects import util


class Move(base_classes.NoOutputAsyncMutator):
  """Move an instance between zones."""

  @property
  def service(self):
    return self.compute.projects

  @property
  def resource_type(self):
    return 'projects'

  @property
  def method(self):
    return 'MoveInstance'

  @property
  def custom_get_requests(self):
    return self._target_to_get_request

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument(
        '--destination-zone',
        completion_resource='compute.zones',
        help='The zone to move the instance to.',
        required=True)

  def CreateRequests(self, args):
    """Returns a request for moving a instance."""

    target_instance = instance_flags.INSTANCE_ARG.ResolveAsResource(
        args, self.resources, scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))
    destination_zone = self.resources.Parse(
        args.destination_zone, collection='compute.zones')

    request = self.messages.ComputeProjectsMoveInstanceRequest(
        instanceMoveRequest=self.messages.InstanceMoveRequest(
            destinationZone=destination_zone.SelfLink(),
            targetInstance=target_instance.SelfLink(),
        ),
        project=self.project,
    )

    destination_instance_ref = self.resources.Parse(
        target_instance.Name(), collection='compute.instances',
        params={'zone': destination_zone.Name()})

    project_ref = self.resources.Parse(
        self.project, collection='compute.projects')
    util.ParseProject(args.name)

    self._target_to_get_request = {}
    self._target_to_get_request[project_ref.SelfLink()] = (
        destination_instance_ref.SelfLink(),
        self.compute.instances,
        self.messages.ComputeInstancesGetRequest(
            instance=target_instance.Name(),
            project=self.project,
            zone=destination_zone.Name()))

    return [request]


Move.detailed_help = {
    'brief': 'Move an instance between zones',
    'DESCRIPTION': """\
        *{command}* facilitates moving a Google Compute Engine virtual machine
        from one zone to another. Moving a virtual machine may incur downtime
        if the guest OS must be shutdown in order to quiesce disk volumes
        prior to snapshotting.

        For example, running:

           $ gcloud compute instances move example-instance-1 --zone us-central1-b --destination-zone us-central1-f

        will move the instance called example-instance-1, currently running in
        us-central1-b, to us-central1-f.
    """}

