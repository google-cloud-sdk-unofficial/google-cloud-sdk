# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Command for listing instances with specific OS inventory data values."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import os
import zlib

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.resource import resource_projector


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListInstances(base.ListCommand):
  """List instances with specific OS inventory data values.

  {command} displays all Google Compute Engine instances in a project matching
  an inventory filter.

  ## EXAMPLES

  To list all instances with OS inventory data in a project in table form, run:

        $ {command}

  To list the URIs of all instances in a project whose hostname equals
  my-instance, run:

        $ {command} --inventory-filter="Hostname=my-instance" --uri

  To list all instances whose OS short name contains rhel, run:

        $ {command} --inventory-filter="ShortName:rhel"
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    parser.display_info.AddUriFunc(utils.MakeGetUriFunc())
    parser.display_info.AddCacheUpdater(completers.InstancesCompleter)
    parser.add_argument(
        '--inventory-filter',
        type=str,
        help="""Filter expression for matching against OS inventory criteria""")

  def _GetGuestAttributesRequest(self, messages, instance_name, project, zone):
    return messages.ComputeInstancesGetGuestAttributesRequest(
        instance=instance_name,
        project=project,
        queryPath='guestInventory/',
        zone=zone)

  def _GetAllGuestInventoryGuestAttributes(self, holder, instances):
    client = holder.client
    messages = client.messages
    project = properties.VALUES.core.project.GetOrFail()

    requests = [
        self._GetGuestAttributesRequest(messages, instance['name'], project,
                                        os.path.basename(instance['zone']))
        for instance in instances
    ]
    responses = holder.client.BatchRequests([(client.apitools_client.instances,
                                              'GetGuestAttributes', request)
                                             for request in requests])

    for response in filter(None, responses):
      for item in response.queryValue.items:
        if item.key == 'InstalledPackages' or item.key == 'PackageUpdates':
          item.value = zlib.decompress(
              base64.b64decode(item.value), zlib.MAX_WBITS | 32)
    return responses

  def _GetInventoryFilteredInstances(self, instances, responses, query):
    filtered_instances = []

    for instance, response in zip(instances, responses):
      # No listing instances without inventory data.
      if instance is not None and response is not None:
        guest_attributes = response.queryValue.items
        guest_attributes_json = resource_projector.MakeSerializable(
            guest_attributes)

        if query.Evaluate(guest_attributes_json):
          filtered_instances.append(instance)

    return filtered_instances

  def Run(self, args):
    query = resource_filter.Compile(args.inventory_filter)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)
    list_implementation = lister.MultiScopeLister(
        client,
        zonal_service=client.apitools_client.instances,
        aggregation_service=client.apitools_client.instances)

    instances_iterator = lister.Invoke(request_data, list_implementation)
    instances = list(instances_iterator)

    responses = self._GetAllGuestInventoryGuestAttributes(holder, instances)
    return self._GetInventoryFilteredInstances(instances, responses, query)
