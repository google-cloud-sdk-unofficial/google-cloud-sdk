# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Cloud VMware Engine capacity allocations client."""

from typing import Any, Generator, Optional

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util
from googlecloudsdk.core import resources


class CapacityAllocationsClient(util.VmwareClientBase):
  """Cloud VMware Engine capacity allocations client."""

  def __init__(self):
    super(CapacityAllocationsClient, self).__init__()
    self.service = self.client.projects_locations_capacityAllocations

  def List(
      self,
      location_resource: resources.Resource,
      filter_expression: Optional[str] = None,
      page_size: Optional[int] = None,
      limit: Optional[int] = None,
  ) -> Generator[Any, None, None]:
    """List capacity allocations in a given location.

    Args:
      location_resource: Location to list allocations in.
      filter_expression: Filter expression for list query.
      page_size: Number of items per page.
      limit: Maximum number of items to return.

    Returns:
      Generator of capacity allocation proto objects.
    """
    request = (
        self.messages.VmwareengineProjectsLocationsCapacityAllocationsListRequest(
            parent=location_resource.RelativeName(),
            filter=filter_expression,
        )
    )
    return list_pager.YieldFromList(
        self.service,
        request,
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
        field='capacityAllocations',
        get_field_func=util.GetFieldAndLogUnreachable,
    )
