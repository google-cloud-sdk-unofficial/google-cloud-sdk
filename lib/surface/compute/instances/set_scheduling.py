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

"""Command for setting scheduling for virtual machine instances."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.core import apis as core_apis


class SetSchedulingInstances(base_classes.NoOutputAsyncMutator):
  """Set scheduling options for Google Compute Engine virtual machine instances.
  """

  @staticmethod
  def Args(parser):
    restart_on_failure = parser.add_argument(
        '--restart-on-failure',
        action='store_true',
        default=None,  # Tri-valued: None => don't change the setting.
        help='Restart instances if they are terminated by Compute Engine.')
    restart_on_failure.detailed_help = """\
        The instances will be restarted if they are terminated by Compute '
        Engine.  This does not affect terminations performed by the user.'
        """

    messages = core_apis.GetMessagesModule('compute', 'v1')
    migration_options = sorted(messages.Scheduling
                               .OnHostMaintenanceValueValuesEnum
                               .to_dict().keys())

    maintenance_policy = parser.add_argument(
        '--maintenance-policy',
        choices=migration_options,
        type=lambda x: x.upper(),
        help=('Specifies the behavior of the instances when their host '
              'machines undergo maintenance.'))
    maintenance_policy.detailed_help = """\
        Specifies the behavior of the instances when their host machines undergo
        maintenance. TERMINATE indicates that the instances should be
        terminated. MIGRATE indicates that the instances should be migrated to a
        new host. Choosing MIGRATE will temporarily impact the performance of
        instances during a migration event.
        """

    parser.add_argument(
        'name',
        metavar='INSTANCE',
        completion_resource='compute.instances',
        help='The name of the instance for which to change scheduling options.')

    flags.AddZoneFlag(
        parser,
        resource_type='instance',
        operation_type='set scheduling settings for')

  @property
  def service(self):
    return self.compute.instances

  @property
  def method(self):
    return 'SetScheduling'

  @property
  def resource_type(self):
    return 'instances'

  def CreateRequests(self, args):
    """Returns a list of request necessary for setting scheduling options."""
    instance_ref = self.CreateZonalReference(args.name, args.zone)

    scheduling_options = self.messages.Scheduling()

    scheduling_options.automaticRestart = args.restart_on_failure

    if args.maintenance_policy:
      scheduling_options.onHostMaintenance = (
          self.messages.Scheduling.OnHostMaintenanceValueValuesEnum(
              args.maintenance_policy))

    request = self.messages.ComputeInstancesSetSchedulingRequest(
        instance=instance_ref.Name(),
        project=self.project,
        scheduling=scheduling_options,
        zone=instance_ref.zone)

    return [request]


SetSchedulingInstances.detailed_help = {
    'brief': ('Set scheduling options for Google Compute Engine virtual '
              'machines'),
    'DESCRIPTION': """\
        *${command}* is used to configure scheduling options for Google Compute
        Engine virtual machines.
        """,
}
