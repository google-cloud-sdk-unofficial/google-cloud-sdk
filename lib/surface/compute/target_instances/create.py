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
"""Command for creating target instances."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instances import (flags as
                                                          instance_flags)
from googlecloudsdk.command_lib.compute.target_instances import flags


class Create(base_classes.BaseAsyncCreator):
  """Create a target instance for handling traffic from a forwarding rule."""

  INSTANCE_ARG = None
  TARGET_INSTANCE_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.INSTANCE_ARG = instance_flags.InstanceArgumentForTargetInstance()
    cls.INSTANCE_ARG.AddArgument(parser)
    cls.TARGET_INSTANCE_ARG = flags.TargetInstanceArgument()
    cls.TARGET_INSTANCE_ARG.AddArgument(
        parser, operation_type='create the target instance in')

    parser.add_argument(
        '--description',
        help='An optional, textual description of the target instance.')

  @property
  def service(self):
    return self.compute.targetInstances

  @property
  def method(self):
    return 'Insert'

  @property
  def resource_type(self):
    return 'targetInstances'

  def CreateRequests(self, args):

    target_instance_ref = self.TARGET_INSTANCE_ARG.ResolveAsResource(
        args,
        self.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(self.compute_client,
                                                         self.project))

    if target_instance_ref.zone and not args.instance_zone:
      args.instance_zone = target_instance_ref.zone

    instance_ref = self.INSTANCE_ARG.ResolveAsResource(args, self.resources)

    if target_instance_ref.zone != instance_ref.zone:
      raise calliope_exceptions.ToolException(
          'Target instance zone must match the virtual machine instance zone.')

    request = self.messages.ComputeTargetInstancesInsertRequest(
        targetInstance=self.messages.TargetInstance(
            description=args.description,
            name=target_instance_ref.Name(),
            instance=instance_ref.SelfLink(),
        ),
        project=self.project,
        zone=target_instance_ref.zone)

    return [request]


Create.detailed_help = {
    'brief': (
        'Create a target instance for handling traffic from a forwarding rule'),
    'DESCRIPTION': """\
        *{command}* is used to create a target instance for handling
        traffic from one or more forwarding rules. Target instances
        are ideal for traffic that should be managed by a single
        source. For more information on target instances, see
        [](https://cloud.google.com/compute/docs/protocol-forwarding/#targetinstances)
        """,
}
