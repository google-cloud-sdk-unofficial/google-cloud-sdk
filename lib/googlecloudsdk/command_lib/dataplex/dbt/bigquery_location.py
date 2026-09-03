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
"""Reads the location of the BigQuery datasets a dbt run materializes into.

Each dataset is read with a BigQuery ``datasets.get`` and its location mapped to
the matching Dataplex region id. Datasets may each live in a different region,
so locations are returned per dataset. A dataset that cannot be read (missing or
no access) or reports no location is omitted from the result.
"""

from __future__ import annotations

from typing import Iterable

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import log

_BIGQUERY_API = 'bigquery'
_BIGQUERY_API_VERSION = 'v2'


def _dataplex_region(bq_location: str) -> str:
  """Maps a BigQuery dataset location to its Dataplex region id.

  BigQuery reports multi-regions upper-cased (``US``, ``EU``) and regions in
  mixed case; Dataplex entry names use the lower-cased form (``us``, ``eu``,
  ``us-central1``).

  Args:
    bq_location: the ``location`` from a BigQuery Dataset resource.

  Returns:
    The lower-cased Dataplex region id.
  """
  return bq_location.strip().lower()


def ResolveDatasetLocations(  # pylint: disable=invalid-name
    datasets: Iterable[tuple[str, str]],
) -> dict[tuple[str, str], str]:
  """Resolves the Dataplex region of each BigQuery dataset via ``datasets.get``.

  Args:
    datasets: iterable of ``(project, dataset)`` pairs.

  Returns:
    A mapping of ``(project, dataset)`` -> lower-cased Dataplex region. Datasets
    that error (not found, no access) or report no location are omitted, so the
    result may be empty or cover only some of the requested datasets.
  """
  pairs = sorted(set(datasets))
  if not pairs:
    return {}
  client = apis.GetClientInstance(_BIGQUERY_API, _BIGQUERY_API_VERSION)
  messages = client.MESSAGES_MODULE
  resolved = {}
  for project, dataset in pairs:
    try:
      got = client.datasets.Get(
          messages.BigqueryDatasetsGetRequest(
              projectId=project, datasetId=dataset
          )
      )
    except apitools_exceptions.HttpError as e:
      log.debug(
          'Could not read BigQuery dataset [%s.%s] for represents (physical) '
          'location: %s',
          project,
          dataset,
          e,
      )
      continue
    if got.location:
      resolved[(project, dataset)] = _dataplex_region(got.location)
  if not resolved:
    # Every lookup failing is a different situation from a dataset or two being
    # unreadable: the caller learns nothing about any dataset, so the
    # co-location filter silently stops filtering.
    log.warning(
        'Could not read the location of any of the {0} BigQuery dataset(s) '
        'this dbt run materializes into, so none could be checked against the '
        'import location. This usually means the BigQuery API is disabled or '
        'the caller lacks bigquery.datasets.get. Links to @bigquery entries '
        'outside the import location are emitted anyway and the import job '
        'reports them as per-link errors; pass --skip-bigquery-link to omit '
        'them.'.format(len(pairs))
    )
  return resolved
