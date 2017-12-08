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
"""Command for configuring autoscaling of a managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import exceptions


class SetAutoscaling(base_classes.BaseAsyncMutator):
  """Set autoscaling parameters of a managed instance group."""

  @property
  def service(self):
    return self.compute.autoscalers

  @property
  def resource_type(self):
    return 'autoscalers'

  @property
  def method(self):
    raise exceptions.ToolException(
        'Internal error: attempted calling method before determining which '
        'method to call.')

  @staticmethod
  def Args(parser):
    managed_instance_groups_utils.AddAutoscalerArgs(parser)
    parser.add_argument(
        'name',
        metavar='NAME',
        completion_resource='compute.instanceGroupManagers',
        help='Managed instance group which autoscaling parameters will be set.')
    utils.AddZoneFlag(
        parser, resource_type='resources', operation_type='update')

  def CreateRequests(self, args):
    managed_instance_groups_utils.ValidateAutoscalerArgs(args)

    igm_ref = self.CreateZonalReference(
        args.name, args.zone, resource_type='instanceGroupManagers')
    # We need the zone name, which might have been passed after prompting.
    # In that case, we get it from the reference.
    zone = args.zone or igm_ref.zone

    managed_instance_groups_utils.AssertInstanceGroupManagerExists(
        igm_ref, self.project, self.messages, self.compute, self.http,
        self.batch_url)

    autoscaler = managed_instance_groups_utils.AutoscalerForMig(
        mig_name=args.name,
        autoscalers=managed_instance_groups_utils.AutoscalersForZones(
            zones=[zone],
            project=self.project,
            compute=self.compute,
            http=self.http,
            batch_url=self.batch_url),
        scope_name=zone,
        scope_type='zone',
        project=self.project)
    autoscaler_name = getattr(autoscaler, 'name', None)
    as_ref = self.CreateZonalReference(autoscaler_name or args.name, zone)
    autoscaler_resource = managed_instance_groups_utils.BuildAutoscaler(
        args, self.messages, as_ref, igm_ref)

    if autoscaler_name is None:
      method = 'Insert'
      request = self.messages.ComputeAutoscalersInsertRequest(
          project=self.project)
      managed_instance_groups_utils.AdjustAutoscalerNameForCreation(
          autoscaler_resource)
      request.autoscaler = autoscaler_resource
    else:
      method = 'Update'
      request = self.messages.ComputeAutoscalersUpdateRequest(
          project=self.project)
      request.autoscaler = as_ref.Name()
      request.autoscalerResource = autoscaler_resource

    request.zone = as_ref.zone
    return ((method, request),)


SetAutoscaling.detailed_help = {
    'brief': 'Set autoscaling parameters of a managed instance group',
    'DESCRIPTION': """\
        *{command}* sets autoscaling parameters of specified managed instance
group.
        """,
}
