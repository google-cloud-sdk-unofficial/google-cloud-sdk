# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Helper class for generating Cloud Logging URLs for Dataproc resources."""


import re

from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from six.moves.urllib import parse


def get_plain_batch_logging_url():
  """Returns the base URL for the Cloud Logging console.

  This is used when parsing batch resource failed.
  """
  logging_base = 'https://console.cloud.google.com/logs/query'
  batch_resource_filter = 'resource.type="cloud_dataproc_batch"'

  return '{}?{}'.format(
      logging_base,
      parse.urlencode({
          'query': batch_resource_filter,
      }),
  )


def get_batch_logging_url(batch):
  """Returns a Cloud Logging URL for the given batch.

  Args:
    batch: The batch to get the Cloud Logging URL for.

  Returns:
    A Cloud Logging URL for the given batch or a plain url without batch info.
  """

  match = re.match(
      r'projects/(?P<project_id>[^/]+)/locations/[^/]+/batches/(?P<batch_id>[^/]+)',
      batch.name,
  )
  if not match:
    return get_plain_batch_logging_url()
  project_id = match.group('project_id')
  batch_id = match.group('batch_id')
  logging_base = 'https://console.cloud.google.com/logs/query'
  batch_resource_filter = 'resource.type="cloud_dataproc_batch"'
  project_query = f'project={project_id}'

  batch_id_filter = f'resource.labels.batch_id="{batch_id}"'
  universe_domain = properties.VALUES.core.universe_domain.Get()
  driver_output_filter = f'log_name="projects/{project_id}/logs/dataproc.{universe_domain}%2Foutput"'
  filters = [
      batch_resource_filter,
      batch_id_filter,
      driver_output_filter,
  ]
  # Pass `query` and `startTime` as Logs Explorer matrix parameters
  # (`/logs/query;query=...;startTime=...`) rather than embedding a
  # `timestamp>=...` restriction in the query. A timestamp expression in the
  # query disables the time-range selector and the "Stream logs" button, which
  # users want while waiting for an active batch. `query` must also be a matrix
  # parameter: a legacy `?query=` parameter is rewritten by the console and
  # drops any existing `;startTime=` matrix parameter.
  matrix_params = [parse.urlencode({'query': '\n'.join(filters)})]
  create_time = getattr(batch, 'createTime', None)
  if create_time:
    try:
      # Batch.createTime is a google.protobuf.Timestamp, which the API returns
      # as an RFC 3339 string in UTC (e.g. "2025-01-01T00:00:00.123456Z").
      # Parse and format explicitly in UTC so the start time never depends on
      # the local timezone of the machine running gcloud (ParseDateTime
      # defaults to local time when the string carries no offset).
      dt = times.ParseDateTime(create_time, tzinfo=times.UTC)
      matrix_params.append(
          parse.urlencode(
              {'startTime': times.FormatDateTime(dt, tzinfo=times.UTC)}
          )
      )
    except times.Error:
      pass

  return '{};{}?{}'.format(
      logging_base,
      ';'.join(matrix_params),
      project_query,
  )


def get_plain_batches_list_url():
  """Returns the base URL for the Dataproc Batches console.

  This is used when parsing batch resource failed.
  """
  dataproc_batches_base = 'https://console.cloud.google.com/dataproc/batches'
  return dataproc_batches_base


def get_dataproc_batch_url(batch):
  """Returns a Dataproc Batch URL for the given batch."""
  match = re.match(
      r'projects/(?P<project_id>[^/]+)/locations/(?P<location>[^/]+)/batches/(?P<batch_id>[^/]+)',
      batch.name,
  )
  if not match:
    return get_plain_batches_list_url()
  project_id = match.group('project_id')
  batch_id = match.group('batch_id')
  location = match.group('location')
  dataproc_batch_url = f'https://console.cloud.google.com/dataproc/batches/{location}/{batch_id}/summary'
  project_query = f'project={project_id}'
  return dataproc_batch_url + '?' + project_query
