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
"""Utility functions for compute accelerator interconnects commands."""

import types
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    TypedDict,
    Union,
)

from apitools.base.protorpclite import messages as protorpc_messages


def _UnpackItems(element: Any) -> Optional[List[Any]]:
  """Extracts an items list from an element if it represents a container."""
  if element is None:
    return None
  if isinstance(element, dict):
    if 'items' in element:
      items = element.get('items')
      if callable(items):
        return None
      return list(items) if items else []
    return None
  if hasattr(element, 'items'):
    items = getattr(element, 'items')
    if not callable(items):
      return list(items) if items else []
  return None


def ExtractAcceleratorInterconnects(responses: Any) -> List[Any]:
  """Extracts and flattens items from list API responses.

  Handles single page objects, multiple unflattened page response objects,
  pre-flattened lists of resource items, and empty response containers.

  Args:
    responses: Single response object, list of response objects, or
      pre-flattened items.

  Returns:
    Flattened list of accelerator interconnect items.
  """
  if not responses:
    return []
  if not isinstance(responses, (list, tuple)):
    unpacked = _UnpackItems(responses)
    if unpacked is not None:
      return unpacked
    return [responses]

  results: List[Any] = []
  for response in responses:
    unpacked = _UnpackItems(response)
    if unpacked is not None:
      results.extend(unpacked)
    else:
      results.append(response)

  return results


def _MakeCapacityPool(
    messages: Any,
    partition_ids: Optional[Sequence[str]] = None,
    capacity_pool: Optional[Sequence[str]] = None,
) -> Any:
  """Constructs CapacityPool message or dict."""
  pool_cls = getattr(messages, 'CapacityPool', None)
  if pool_cls:
    if partition_ids:
      return pool_cls(partitionIds=list(partition_ids))
    if capacity_pool:
      return pool_cls(resources=list(capacity_pool))
    return pool_cls()
  else:
    if partition_ids:
      return {'partitionIds': list(partition_ids)}
    if capacity_pool:
      return {'resources': list(capacity_pool)}
    return {}


def _MakeAcceleratorInterconnect(
    messages: Any,
    name: str,
    accelerator_topology: Optional[str] = None,
    partition_ids: Optional[Sequence[str]] = None,
    capacity_pool: Optional[Sequence[str]] = None,
    description: Optional[str] = None,
    reactivation_mode: Optional[str] = None,
    labels: Optional[Any] = None,
) -> Any:
  """Constructs AcceleratorInterconnect message or dict."""
  interconnect_cls = getattr(messages, 'AcceleratorInterconnect', None)
  if interconnect_cls:
    interconnect = interconnect_cls(name=name)
    if accelerator_topology:
      interconnect.acceleratorTopology = accelerator_topology
    if description:
      interconnect.description = description
    if reactivation_mode:
      mode_upper = reactivation_mode.upper()
      if hasattr(interconnect_cls, 'ReactivationModeValueValuesEnum'):
        mode_enum = getattr(
            interconnect_cls.ReactivationModeValueValuesEnum,
            mode_upper,
            None,
        )
        interconnect.reactivationMode = mode_enum or mode_upper
      else:
        interconnect.reactivationMode = mode_upper

    if partition_ids or capacity_pool:
      params_cls = getattr(messages, 'AcceleratorInterconnectParams', None)
      capacity_pool_obj = _MakeCapacityPool(
          messages, partition_ids=partition_ids, capacity_pool=capacity_pool
      )
      if params_cls:
        interconnect.params = params_cls(capacityPool=capacity_pool_obj)
      else:
        interconnect.params = capacity_pool_obj

    if labels is not None:
      labels_cls = getattr(
          interconnect_cls,
          'LabelsValue',
          getattr(messages, 'AcceleratorInterconnectLabelsValue', None),
      )
      if labels_cls and isinstance(labels, dict):
        prop_cls = getattr(labels_cls, 'AdditionalProperty', None)
        if prop_cls:
          interconnect.labels = labels_cls(
              additionalProperties=[
                  prop_cls(key=k, value=v) for k, v in labels.items()
              ]
          )
        else:
          interconnect.labels = labels
      else:
        interconnect.labels = labels
    return interconnect
  else:
    interconnect = {'name': name}
    if accelerator_topology:
      interconnect['acceleratorTopology'] = accelerator_topology
    if description:
      interconnect['description'] = description
    if reactivation_mode:
      interconnect['reactivationMode'] = reactivation_mode.upper()
    if partition_ids or capacity_pool:
      interconnect['params'] = {
          'capacityPool': _MakeCapacityPool(
              messages,
              partition_ids=partition_ids,
              capacity_pool=capacity_pool,
          )
      }
    if labels is not None:
      interconnect['labels'] = labels
    return interconnect


def MakeCreateRequest(
    messages: Any,
    project: str,
    zone: str,
    name: str,
    accelerator_topology: Optional[str] = None,
    partition_ids: Optional[Sequence[str]] = None,
    capacity_pool: Optional[Sequence[str]] = None,
    description: Optional[str] = None,
    reactivation_mode: Optional[str] = None,
    labels: Optional[Any] = None,
) -> Any:
  """Constructs an Insert request for an accelerator interconnect."""
  interconnect = _MakeAcceleratorInterconnect(
      messages=messages,
      name=name,
      accelerator_topology=accelerator_topology,
      partition_ids=partition_ids,
      capacity_pool=capacity_pool,
      description=description,
      reactivation_mode=reactivation_mode,
      labels=labels,
  )
  req_class = getattr(
      messages,
      'ComputeAcceleratorInterconnectsInsertRequest',
      None,
  ) or getattr(
      messages,
      'AcceleratorInterconnectsInsertRequest',
      None,
  )

  valid_fields = None
  if isinstance(req_class, type) and hasattr(req_class, 'all_fields'):
    valid_fields = {f.name for f in req_class.all_fields()}

  insert_req_cls = getattr(
      messages, 'AcceleratorInterconnectsInsertRequest', None
  )
  if insert_req_cls:
    insert_body = insert_req_cls(resource=interconnect)
  else:
    insert_body = {'resource': interconnect}

  kwargs: Dict[str, Any] = {'project': project, 'zone': zone}
  if valid_fields is not None:
    if 'acceleratorInterconnectsInsertRequest' in valid_fields:
      kwargs['acceleratorInterconnectsInsertRequest'] = insert_body
    elif 'acceleratorInterconnect' in valid_fields:
      kwargs['acceleratorInterconnect'] = interconnect
  else:
    kwargs['acceleratorInterconnectsInsertRequest'] = insert_body

  if req_class:
    try:
      request = req_class(**kwargs)
    except TypeError:
      kwargs.pop('acceleratorInterconnectsInsertRequest', None)
      kwargs['acceleratorInterconnect'] = interconnect
      request = req_class(**kwargs)
  else:
    kwargs['acceleratorInterconnect'] = interconnect
    request = kwargs

  if not hasattr(type(request), 'all_fields'):
    if isinstance(request, dict):
      request['acceleratorInterconnect'] = interconnect
    else:
      setattr(request, 'acceleratorInterconnect', interconnect)

  return request


def MakeDeleteRequest(
    messages: Any, project: str, zone: str, name: str
) -> Any:
  """Constructs a Delete request for an accelerator interconnect."""
  req_class = getattr(
      messages,
      'ComputeAcceleratorInterconnectsDeleteRequest',
      None,
  ) or getattr(
      messages,
      'AcceleratorInterconnectsDeleteRequest',
      None,
  )
  if req_class:
    return req_class(
        project=project,
        zone=zone,
        acceleratorInterconnect=name,
    )
  return {
      'project': project,
      'zone': zone,
      'acceleratorInterconnect': name,
  }


def MakeDescribeRequest(
    messages: Any, project: str, zone: str, name: str
) -> Any:
  """Constructs a Get/Describe request for an accelerator interconnect."""
  req_class = getattr(
      messages,
      'ComputeAcceleratorInterconnectsGetRequest',
      None,
  ) or getattr(
      messages,
      'AcceleratorInterconnectsGetRequest',
      None,
  )
  if req_class:
    return req_class(
        project=project,
        zone=zone,
        acceleratorInterconnect=name,
    )
  return {
      'project': project,
      'zone': zone,
      'acceleratorInterconnect': name,
  }


def MakeListRequest(
    messages: types.ModuleType,
    project: str,
    zone: str,
    filter_expr: Optional[str] = None,
    max_results: Optional[int] = None,
    page_token: Optional[str] = None,
    return_partial_success: Optional[bool] = None,
) -> Union[protorpc_messages.Message, Dict[str, Union[str, int, bool]]]:
  """Constructs a List request for accelerator interconnects."""
  req_class = getattr(
      messages,
      'ComputeAcceleratorInterconnectsListRequest',
      None,
  ) or getattr(
      messages,
      'AcceleratorInterconnectsListRequest',
      None,
  )
  kwargs: Dict[str, Union[str, int, bool]] = {'project': project, 'zone': zone}
  if filter_expr is not None:
    kwargs['filter'] = filter_expr
  if max_results is not None:
    kwargs['maxResults'] = max_results
  if page_token is not None:
    kwargs['pageToken'] = page_token
  if return_partial_success is not None:
    kwargs['returnPartialSuccess'] = return_partial_success

  if req_class:
    if isinstance(req_class, type) and hasattr(req_class, 'all_fields'):
      valid_fields = {f.name for f in req_class.all_fields()}
      filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}
      return req_class(**filtered_kwargs)
    return req_class(**kwargs)
  return kwargs


PartitionFormabilityRecord = TypedDict(
    'PartitionFormabilityRecord',
    {
        'partitionId': str,
        'acceleratorTopology': str,
        'state': str,
        'infrastructureHealth': str,
        'instanceState': str,
        'usageState': str,
        'subblock': str,
        'parent': str,
    },
)


FormabilityRecord = PartitionFormabilityRecord


def ParseSubblocks(
    subblocks: Optional[Sequence[str]] = None,
    subblocks_flag: Optional[Sequence[str]] = None,
) -> List[str]:
  """Parses, deduplicates, and concatenates subblock inputs."""
  combined: List[str] = []
  seen = set()
  for source in (subblocks, subblocks_flag):
    if not source:
      continue
    if isinstance(source, str):
      candidates = [source]
    else:
      candidates = list(source)
    for item in candidates:
      item_str = str(item).strip() if item is not None else ''
      if item_str and item_str not in seen:
        seen.add(item_str)
        combined.append(item_str)
  return combined


def TransformFormabilityItem(
    item: Any, topology_filter: Optional[str] = None
) -> Optional[PartitionFormabilityRecord]:
  """Pure transform of a single proto/dict item into a record."""
  if item is None:
    return None

  if isinstance(item, dict):
    partition_id = item.get('partitionId') or item.get('partition_id')
    accelerator_topology = item.get('acceleratorTopology') or item.get(
        'accelerator_topology'
    )
    status = item.get('status')
    parent = item.get('parent')
    subblock = item.get('subblock')
  else:
    partition_id = getattr(item, 'partitionId', None) or getattr(
        item, 'partition_id', None
    )
    accelerator_topology = (
        getattr(item, 'acceleratorTopology', None)
        or getattr(item, 'accelerator_topology', None)
    )
    status = getattr(item, 'status', None)
    parent = getattr(item, 'parent', None)
    subblock = getattr(item, 'subblock', None)

  if topology_filter and accelerator_topology != topology_filter:
    return None

  state = None
  infra_health = None
  instance_state = None
  usage_state = None

  if status:
    if isinstance(status, dict):
      state = status.get('state')
      infra_health = status.get('infrastructureHealth') or status.get(
          'infrastructure_health'
      )
      instance_state = status.get('instanceState') or status.get(
          'instance_state'
      )
      usage_state = status.get('usageState') or status.get('usage_state')
    else:
      state = getattr(status, 'state', None)
      infra_health = getattr(status, 'infrastructureHealth', None) or getattr(
          status, 'infrastructure_health', None
      )
      instance_state = getattr(status, 'instanceState', None) or getattr(
          status, 'instance_state', None
      )
      usage_state = getattr(status, 'usageState', None) or getattr(
          status, 'usage_state', None
      )

  subblock_name = str(subblock).split('/')[-1] if subblock else '-'

  return {
      'partitionId': str(partition_id or '-'),
      'acceleratorTopology': str(accelerator_topology or '-'),
      'state': str(state or '-'),
      'infrastructureHealth': str(infra_health or '-'),
      'instanceState': str(instance_state or '-'),
      'usageState': str(usage_state or '-'),
      'subblock': subblock_name,
      'parent': str(parent or '-'),
  }


def TransformFormabilityResponse(
    response: Any, topology_filter: Optional[str] = None
) -> List[PartitionFormabilityRecord]:
  """Pure transform of the top-level response container into records."""
  if not response:
    return []

  if isinstance(response, (list, tuple)):
    items = response
  elif isinstance(response, dict):
    items = response.get('items')
    if callable(items):
      items = None
  else:
    items = getattr(response, 'items', None)
    if callable(items):
      items = None

  if not items:
    return []

  records: List[PartitionFormabilityRecord] = []
  for item in items:
    record = TransformFormabilityItem(item, topology_filter=topology_filter)
    if record is not None:
      records.append(record)
  return records


def MakeQueryFormabilityRequest(
    messages: Any, project: str, zone: str, subblocks: Sequence[str]
) -> Any:
  """Constructs a QueryFormability request across partition trees."""
  subblocks_list = list(subblocks)
  body = None
  body_class = getattr(messages, 'QueryFormabilityRequest', None)
  if body_class:
    body = body_class(subblocks=subblocks_list)

  req_class = getattr(
      messages,
      'ComputeAcceleratorInterconnectsQueryFormabilityRequest',
      None,
  ) or getattr(
      messages,
      'AcceleratorInterconnectsQueryFormabilityRequest',
      None,
  )

  if req_class:
    try:
      return req_class(
          project=project,
          zone=zone,
          queryFormabilityRequest=body if body else subblocks_list,
      )
    except (TypeError, AttributeError):
      return req_class(
          project=project,
          zone=zone,
          subblocks=subblocks_list,
      )
  return {
      'project': project,
      'zone': zone,
      'subblocks': subblocks_list,
  }


MemberInstanceRecord = TypedDict(
    'MemberInstanceRecord',
    {
        'instance': str,
        'instance_id': Union[int, str],
        'instanceId': Union[int, str],
        'id': Union[int, str],
        'zone': str,
    },
)


def GetMemberInstanceUri(resource: Any) -> str:
  """Returns the selfLink or URL for a member instance resource."""
  if isinstance(resource, dict):
    return resource.get('instance') or ''
  return getattr(resource, 'instance', None) or ''


def FormatMemberInstances(
    responses: Any, zone: Optional[str] = None
) -> List[MemberInstanceRecord]:
  """Extracts member instances from API responses and returns formatted records.
  """
  items = ExtractAcceleratorInterconnects(responses)
  results: List[MemberInstanceRecord] = []
  for item in items:
    if isinstance(item, dict):
      instance_url = item.get('instance') or ''
      instance_id = item.get('instanceId')
      if instance_id is None:
        instance_id = item.get('instance_id')
      if instance_id is None:
        instance_id = item.get('id', '')
    else:
      instance_url = getattr(item, 'instance', None) or ''
      instance_id = getattr(
          item,
          'instanceId',
          getattr(item, 'instance_id', getattr(item, 'id', '')),
      )
      if instance_id is None:
        instance_id = ''

    results.append({
        'instance': instance_url,
        'instance_id': instance_id,
        'instanceId': instance_id,
        'id': instance_id,
        'zone': zone or '',
    })
  return results


def MakeMemberInstancesListRequest(
    messages: Any,
    project: str,
    zone: str,
    interconnect_name: str,
    filter_expr: Optional[str] = None,
    max_results: Optional[int] = None,
    page_token: Optional[str] = None,
    return_partial_success: Optional[bool] = None,
) -> Any:
  """Constructs a list request for member instances of an interconnect."""
  req_class = (
      getattr(
          messages,
          'ComputeAcceleratorInterconnectMemberInstancesListRequest',
          None,
      )
      or getattr(
          messages,
          'AcceleratorInterconnectMemberInstancesListRequest',
          None,
      )
      or getattr(
          messages,
          'ComputeAcceleratorInterconnectsListMemberInstancesRequest',
          None,
      )
  )
  request_kwargs: Dict[str, Any] = {
      'project': project,
      'zone': zone,
      'acceleratorInterconnect': interconnect_name,
  }
  if filter_expr is not None:
    request_kwargs['filter'] = filter_expr
  if max_results is not None:
    request_kwargs['maxResults'] = max_results
  if page_token is not None:
    request_kwargs['pageToken'] = page_token
  if return_partial_success is not None:
    request_kwargs['returnPartialSuccess'] = return_partial_success

  if req_class:
    if isinstance(req_class, type) and hasattr(req_class, 'all_fields'):
      field_names = {f.name for f in req_class.all_fields()}
      if (
          'parent_name' in field_names
          and 'acceleratorInterconnect' not in field_names
      ):
        request_kwargs.pop('acceleratorInterconnect', None)
        request_kwargs['parent_name'] = interconnect_name
      filtered_kwargs = {
          k: v for k, v in request_kwargs.items() if k in field_names
      }
      return req_class(**filtered_kwargs)
    request = req_class(**request_kwargs)
    if not hasattr(type(request), 'all_fields'):
      if isinstance(request, dict):
        request['acceleratorInterconnect'] = interconnect_name
        request['project'] = project
        request['zone'] = zone
      else:
        if not hasattr(request, 'acceleratorInterconnect'):
          setattr(request, 'acceleratorInterconnect', interconnect_name)
        if not hasattr(request, 'project'):
          setattr(request, 'project', project)
        if not hasattr(request, 'zone'):
          setattr(request, 'zone', zone)
    return request
  return request_kwargs
