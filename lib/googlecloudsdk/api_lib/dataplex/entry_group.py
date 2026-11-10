# -*- coding: utf-8 -*- #
# Copyright 2024 Google Inc. All Rights Reserved.
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
"""Client for interaction with EntryGroup API CRUD DATAPLEX."""

from collections.abc import Sequence
from typing import Any

from apitools.base.py import encoding
from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.generated_clients.apis.dataplex.v1 import dataplex_v1_messages


def GenerateEntryGroupForCreateRequest(args):
  """Create Entry Group Request."""
  module = dataplex_api.GetMessageModule()
  request = module.GoogleCloudDataplexV1EntryGroup(
      description=args.description,
      displayName=args.display_name,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1EntryGroup,
                                       args))
  return request


def GenerateEntryGroupForUpdateRequest(args):
  """Update Entry Group Request."""
  module = dataplex_api.GetMessageModule()
  return module.GoogleCloudDataplexV1EntryGroup(
      description=args.description,
      displayName=args.display_name,
      etag=args.etag,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1EntryGroup,
                                       args))


def GenerateEntryGroupUpdateMask(args):
  """Create Update Mask for EntryGroup."""
  update_mask = []
  if args.IsSpecified('description'):
    update_mask.append('description')
  if args.IsSpecified('display_name'):
    update_mask.append('displayName')
  if args.IsSpecified('labels'):
    update_mask.append('labels')
  return update_mask


def GetEntryGroup(entry_group_name):
  """Fetches an EntryGroup by its relative resource name.

  Args:
    entry_group_name: the relative resource name of the entry group
      (projects/{p}/locations/{l}/entryGroups/{eg}).

  Returns:
    The GoogleCloudDataplexV1EntryGroup message.

  Raises:
    apitools.base.py.exceptions.HttpError: if the entry group does not exist or
      is not accessible.
  """
  return dataplex_api.GetClientInstance().projects_locations_entryGroups.Get(
      dataplex_api.GetMessageModule()
      .DataplexProjectsLocationsEntryGroupsGetRequest(name=entry_group_name)
  )


def WaitForOperation(operation):
  """Waits for the given google.longrunning.Operation to complete."""
  return dataplex_api.WaitForOperation(
      operation,
      dataplex_api.GetClientInstance().projects_locations_entryGroups)


def EntryGroupSetIamPolicy(entry_group_ref, policy):
  """Set Iam Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsEntryGroupsSetIamPolicyRequest(
      resource=entry_group_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule()
      .GoogleIamV1SetIamPolicyRequest(policy=policy))
  return dataplex_api.GetClientInstance(
  ).projects_locations_entryGroups.SetIamPolicy(set_iam_policy_req)


def EntryGroupGetIamPolicy(entry_group_ref):
  """Get Iam Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsEntryGroupsGetIamPolicyRequest(
      resource=entry_group_ref.RelativeName())
  return dataplex_api.GetClientInstance(
  ).projects_locations_entryGroups.GetIamPolicy(get_iam_policy_req)


def EntryGroupAddIamPolicyBinding(entry_group_ref, member, role):
  """Add IAM policy binding request."""
  policy = EntryGroupGetIamPolicy(entry_group_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role)
  return EntryGroupSetIamPolicy(entry_group_ref, policy)


def EntryGroupRemoveIamPolicyBinding(entry_group_ref, member, role):
  """Remove IAM policy binding request."""
  policy = EntryGroupGetIamPolicy(entry_group_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return EntryGroupSetIamPolicy(entry_group_ref, policy)


def EntryGroupSetIamPolicyFromFile(entry_group_ref, policy_file):
  """Set IAM policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file,
      dataplex_api.GetMessageModule().GoogleIamV1Policy)
  return EntryGroupSetIamPolicy(entry_group_ref, policy)


def BatchChangeMetadata(
    entry_group_ref: resources.Resource,
    changes: Sequence[
        dataplex_v1_messages.GoogleCloudDataplexV1BatchChangeMetadataRequestChange
    ],
    description: str | None = None,
) -> dataplex_v1_messages.GoogleLongrunningOperation.ResponseValue | None:
  """Applies a batch of metadata changes to an entry group.

  Sends a BatchChangeMetadata request and waits for the resulting long-running
  operation to finish.

  Args:
    entry_group_ref: The entry group to apply the changes to.
    changes: The metadata changes to apply.
    description: Text description of the batch change.

  Returns:
    The response of the finished operation. Pass this response to
    GetFailedRequests to get the changes that failed.

  Raises:
    apitools.base.py.exceptions.HttpError: If the service rejects the request.
    waiter.OperationError: If the operation fails, for example because none of
      the changes could be applied.
  """
  messages = dataplex_api.GetMessageModule()
  request = messages.GoogleCloudDataplexV1BatchChangeMetadataRequest(
      name=entry_group_ref.RelativeName(), changes=list(changes)
  )
  if description is not None:
    request.description = (
        messages.GoogleCloudDataplexV1BatchChangeMetadataRequestDescription(
            content=description
        )
    )
  client = dataplex_api.GetClientInstance()
  operation = client.projects_locations_entryGroups.BatchChangeMetadata(request)
  operation_ref = resources.REGISTRY.Parse(
      operation.name, collection='dataplex.projects.locations.operations'
  )
  return waiter.WaitFor(
      BatchOperationPoller(client.projects_locations_operations),
      operation_ref,
      f'Waiting for [{operation_ref.RelativeName()}] to finish',
  )


def GetFailedRequests(
    message: (
        dataplex_v1_messages.GoogleLongrunningOperation.ResponseValue
        | dataplex_v1_messages.GoogleLongrunningOperation.MetadataValue
        | None
    ),
) -> dict[int, dict[str, Any]]:
  """Returns the failed changes of a BatchChangeMetadata operation.

  Args:
    message: The `response` or `metadata` of a BatchChangeMetadata operation.

  Returns:
    A dict that maps the 0-based position of each failed change in the request
    to its `google.rpc.Status` dict (for example,
    `{'code': 5, 'message': '...'}`), ordered by position. The dict is empty if
    no change failed.
  """
  if message is None:
    return {}
  failed_requests = (
      encoding.MessageToPyValue(message).get('failedRequests') or {}
  )
  return dict(sorted((int(k), v) for k, v in failed_requests.items()))


class BatchOperationPoller(waiter.CloudOperationPollerNoResources):
  """Poller for BatchChangeMetadata long-running operations.

  When none of the changes in a batch can be applied, the operation fails with
  a generic error, and the errors of the individual changes are only available
  in the operation metadata. Unlike the base class, this poller includes them
  in the raised error.
  """

  def IsDone(
      self, operation: dataplex_v1_messages.GoogleLongrunningOperation
  ) -> bool:
    """Returns whether the operation finished successfully.

    Args:
      operation: The BatchChangeMetadata long-running operation.

    Returns:
      True if the operation finished successfully, False if it is still
      running.

    Raises:
      waiter.OperationError: If the operation finished with an error. The
        message includes the errors of the individual changes, if any.
    """
    if not operation.done:
      return False
    if not operation.error:
      return True
    lines = [operation.error.message] if operation.error.message else []
    failed_requests = GetFailedRequests(operation.metadata)
    if failed_requests:
      lines.append(yaml.dump({'failedRequests': failed_requests}).rstrip())
    raise waiter.OperationError('\n'.join(lines))
