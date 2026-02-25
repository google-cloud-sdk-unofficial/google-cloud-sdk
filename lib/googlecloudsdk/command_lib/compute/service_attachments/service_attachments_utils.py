# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple service-attachments subcommands."""


import six


def GetConnectionPreference(args, messages):
  """Get connection preference of the service attachment."""
  if args.connection_preference == 'ACCEPT_AUTOMATIC':
    return messages.ServiceAttachment.ConnectionPreferenceValueValuesEnum.ACCEPT_AUTOMATIC
  if args.connection_preference == 'ACCEPT_MANUAL':
    return messages.ServiceAttachment.ConnectionPreferenceValueValuesEnum.ACCEPT_MANUAL

  return None


def GetConsumerAcceptList(args, messages):
  """Get consumer accept list of the service attachment."""
  consumer_accept_list = []
  for project_limit in args.consumer_accept_list:
    for project_id_or_network_url, conn_limit in sorted(
        six.iteritems(project_limit)
    ):
      if '/networks/' in project_id_or_network_url:
        consumer_accept_list.append(
            messages.ServiceAttachmentConsumerProjectLimit(
                networkUrl=project_id_or_network_url,
                connectionLimit=int(conn_limit),
            )
        )
      elif '/forwardingRules/' in project_id_or_network_url:
        raise ValueError(
            'Private Service Connect Endpoint URL is not supported for consumer'
            ' accept list'
        )
      else:
        consumer_accept_list.append(
            messages.ServiceAttachmentConsumerProjectLimit(
                projectIdOrNum=project_id_or_network_url,
                connectionLimit=int(conn_limit),
            )
        )
  return consumer_accept_list


def GetConsumerAcceptListWithEndpointBasedSecurity(args, messages):
  """Get consumer accept list of the service attachment with endpoint based security supported."""
  consumer_accept_list = []
  for project_limit in args.consumer_accept_list:
    for consumer_entry, conn_limit_raw in sorted(six.iteritems(project_limit)):
      # Accept list with network URL.
      if '/networks/' in consumer_entry:
        if not conn_limit_raw:
          raise ValueError(
              f'Connection limit is required for network URL: {consumer_entry}'
          )
        consumer_accept_list.append(
            messages.ServiceAttachmentConsumerProjectLimit(
                networkUrl=consumer_entry,
                connectionLimit=int(conn_limit_raw),
            )
        )
      # Accept list with endpoint URL.
      elif '/forwardingRules/' in consumer_entry:
        if conn_limit_raw:
          consumer_accept_list.append(
              messages.ServiceAttachmentConsumerProjectLimit(
                  endpointUrl=consumer_entry,
                  connectionLimit=int(conn_limit_raw),
              )
          )
        else:
          consumer_accept_list.append(
              messages.ServiceAttachmentConsumerProjectLimit(
                  endpointUrl=consumer_entry
              )
          )
      else:
        # Accept list with project ID or number.
        if not conn_limit_raw:
          raise ValueError(
              'Connection limit is required for project ID or number:'
              f' {consumer_entry}'
          )
        consumer_accept_list.append(
            messages.ServiceAttachmentConsumerProjectLimit(
                projectIdOrNum=consumer_entry,
                connectionLimit=int(conn_limit_raw),
            )
        )
  return consumer_accept_list


def GetConnectedEndpointIds(service_attachment):
  """Get connected endpoint resource IDs from service attachment."""
  return set(
      ep.endpointWithId.rstrip('/').split('/')[-1]
      for ep in service_attachment.connectedEndpoints or []
      if ep.endpointWithId
  )


def CleanObsoleteAcceptedEndpointUrls(
    service_attachment, connected_endpoint_ids, cleared_fields
):
  """Removes consumer accept list entries with endpointUrls that are not in connectedEndpoints."""
  if not service_attachment.consumerAcceptLists:
    return False

  old_accept_list_len = len(service_attachment.consumerAcceptLists)
  # Use IDs for comparison to handle Project ID vs Project Number mismatches
  service_attachment.consumerAcceptLists = list(
      filter(
          lambda entry: (
              not entry.endpointUrl
              or entry.endpointUrl.rstrip('/').split('/')[-1]
              in connected_endpoint_ids
          ),
          service_attachment.consumerAcceptLists,
      )
  )
  cleaned_accept_list = service_attachment.consumerAcceptLists
  cleaned_accept_list_len = len(cleaned_accept_list)

  # If list length has changed, it means obsolete entries were removed.
  if cleaned_accept_list_len == old_accept_list_len:
    return False

  if not cleaned_accept_list and 'consumerAcceptLists' not in cleared_fields:
    # If all entries are removed, we need to clear consumerAcceptLists.
    cleared_fields.append('consumerAcceptLists')
  elif cleaned_accept_list and 'consumerAcceptLists' in cleared_fields:
    cleared_fields.remove('consumerAcceptLists')
  return True


def CleanObsoleteRejectedEndpointUrls(
    service_attachment, connected_endpoint_ids, cleared_fields
):
  """Removes consumer reject list entries with endpointUrls that are not in connectedEndpoints."""
  if not service_attachment.consumerRejectLists:
    return False

  old_reject_list_len = len(service_attachment.consumerRejectLists)
  service_attachment.consumerRejectLists = list(
      filter(
          lambda entry: (
              '/forwardingRules/' not in entry
              or entry.rstrip('/').split('/')[-1] in connected_endpoint_ids
          ),
          service_attachment.consumerRejectLists,
      )
  )
  cleaned_reject_list = service_attachment.consumerRejectLists
  cleaned_reject_list_len = len(cleaned_reject_list)

  # If list length has changed, it means obsolete entries were removed.
  if cleaned_reject_list_len == old_reject_list_len:
    return False

  if not cleaned_reject_list and 'consumerRejectLists' not in cleared_fields:
    # If all entries are removed, we need to clear consumerRejectLists.
    cleared_fields.append('consumerRejectLists')
  elif cleaned_reject_list and 'consumerRejectLists' in cleared_fields:
    cleared_fields.remove('consumerRejectLists')
  return True
