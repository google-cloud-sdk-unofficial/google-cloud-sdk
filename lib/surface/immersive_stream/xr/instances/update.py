# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to update an Immersive Stream for XR service instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.immersive_stream.xr import api_util
from googlecloudsdk.api_lib.immersive_stream.xr import instances
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.immersive_stream.xr import flags
from googlecloudsdk.command_lib.immersive_stream.xr import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Update an Immersive Stream for XR service instance."""

  detailed_help = {
      'DESCRIPTION': ("""
          Update an Immersive Stream for XR service instance.
          This command can either be used to update the capacity for an existing
          region of the service instance or to update the content build version
          served by the instance.
          If updating the capacity, only one region may be updated for each
          command execution, and the new capacity may not be 0 or exceed the
          quota limit.
      """),
      'EXAMPLES': ("""
          To update the service instance 'my-instance' to have capacity 2 for an
          existing region us-west1, run:

            $ {command} my-instance --update-region=region=us-west1,capacity=2

          To update the service instance 'my-instance' to have capacity 1 for a
          new region us-east4, run:

            $ {command} my-instance --add-region=region=us-east4,capacity=1

          To update the service instance 'my-instance' to remove the existing
          region us-east4, run:

            $ {command} my-instance --remove-region=us-east4

          To update the service instance 'my-instance' to serve content version
          `my-version`, run:

            $ {command} my-instance --version=my-version
      """)
  }

  @staticmethod
  def Args(parser):
    resource_args.AddInstanceResourceArg(parser, verb='to update')
    group = parser.add_group(mutex=True, required=True, help='Update options')
    group.add_argument(
        '--version',
        help='Build version tag of the content served by this instance')
    flags.AddRegionConfigArg(
        '--add-region', group, repeatable=False, required=False)
    flags.AddRegionConfigArg(
        '--update-region', group, repeatable=False, required=False)
    group.add_argument(
        '--remove-region', help='Region to remove', action='append')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    version = args.version
    add_region_configs = args.add_region
    remove_regions = args.remove_region
    update_region_configs = args.update_region
    instance_name = args.instance

    instance_ref = resources.REGISTRY.Parse(
        None,
        collection='stream.projects.locations.streamInstances',
        api_version='v1alpha1',
        params={
            'projectsId': properties.VALUES.core.project.Get(required=True),
            'locationsId': 'global',
            'streamInstancesId': instance_name
        })

    if version:
      result_operation = instances.UpdateContentBuildVersion(
          instance_ref, version)
    else:
      # We limit to one update per call.
      if add_region_configs:
        if len(add_region_configs) > 1:
          log.status.Print(('Only one region may be added at a time. Please '
                            'try again with only one --add-region argument.'))
          return
      elif remove_regions:
        if len(remove_regions) > 1:
          log.status.Print(
              ('Only one region may be removed at a time. Please '
               'try again with only one --remove-region argument.'))
          return
      elif update_region_configs:
        if len(update_region_configs) > 1:
          log.status.Print(
              ('Only one region may be updated at a time. Please '
               'try again with only one --update-region argument.'))
          return

      current_instance = instances.Get(instance_ref.RelativeName())
      target_location_configs = instances.GenerateTargetLocationConfigs(
          add_region_configs=add_region_configs,
          update_region_configs=update_region_configs,
          remove_regions=remove_regions,
          current_instance=current_instance)
      if target_location_configs is None:
        return
      result_operation = instances.UpdateLocationConfigs(
          instance_ref, target_location_configs)

    client = api_util.GetClient()

    log.status.Print('Update request issued for: [{}]'.format(instance_name))
    if args.async_:
      log.status.Print('Check operation [{}] for status.\n'.format(
          result_operation.name))
      return result_operation

    operation_resource = resources.REGISTRY.Parse(
        result_operation.name,
        collection='stream.projects.locations.operations',
        api_version='v1alpha1')
    updated_instance = waiter.WaitFor(
        waiter.CloudOperationPoller(client.projects_locations_streamInstances,
                                    client.projects_locations_operations),
        operation_resource,
        'Waiting for operation [{}] to complete'.format(result_operation.name))

    instance_resource = resources.REGISTRY.Parse(
        None,
        collection='stream.projects.locations.streamInstances',
        api_version='v1alpha1',
        params={
            'projectsId': properties.VALUES.core.project.Get(required=True),
            'locationsId': 'global',
            'streamInstancesId': instance_name
        })

    log.UpdatedResource(instance_resource)
    return updated_instance
