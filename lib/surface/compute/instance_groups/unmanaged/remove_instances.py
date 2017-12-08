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
"""Command for removing instances from unmanaged instance groups."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


class RemoveInstances(base_classes.NoOutputAsyncMutator):
  """Removes instances from unmanaged instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.ZONAL_INSTANCE_GROUP_ARG.AddArgument(parser)

    parser.add_argument(
        '--instances',
        required=True,
        type=arg_parsers.ArgList(min_length=1),
        metavar='INSTANCE',
        help='The names of the instances to remove from the instance group.')

  @property
  def service(self):
    return self.compute.instanceGroups

  @property
  def method(self):
    return 'RemoveInstances'

  @property
  def resource_type(self):
    return 'instanceGroups'

  def CreateRequests(self, args):
    group_ref = (
        instance_groups_flags.ZONAL_INSTANCE_GROUP_ARG.ResolveAsResource(
            args, self.resources,
            default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=flags.GetDefaultScopeLister(
                self.compute_client, self.project)))

    instance_references = []
    for instance in args.instances:
      ref = self.resources.Parse(
          instance, params={'zone': group_ref.zone},
          collection='compute.instances')
      instance_references.append(ref)

    instance_groups_utils.ValidateInstanceInZone(instance_references,
                                                 group_ref.zone)

    instance_references = [
        self.messages.InstanceReference(instance=inst.SelfLink())
        for inst in instance_references]
    request_payload = self.messages.InstanceGroupsRemoveInstancesRequest(
        instances=instance_references)

    request = self.messages.ComputeInstanceGroupsRemoveInstancesRequest(
        instanceGroup=group_ref.Name(),
        instanceGroupsRemoveInstancesRequest=request_payload,
        zone=group_ref.zone,
        project=group_ref.project
    )

    return [request]

  detailed_help = {
      'brief': ('Removes resources from an unmanaged instance group '
                'by instance name'),
      'DESCRIPTION': """\
          *{command}* removes instances from an unmanaged instance group using
          the instance name.

          This does not delete the actual instance resources but removes
          it from the instance group.
          """,
  }
