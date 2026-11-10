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
"""Utilities for the Assured Workloads Data Boundary compliance endpoints."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.assured import util
from googlecloudsdk.core import exceptions

# Only organization scoped parents are supported by the API today. Folder and
# project scopes can be added here once the API supports them.
_SCOPE_PREFIXES = {
    'organizations': 'Organizations',
}


class UnsupportedScopeError(exceptions.Error):
  """Raised when a resource name has an unsupported parent scope."""


def _GetScope(resource_name):
  """Returns the scope collection of the resource name."""
  scope = resource_name.split('/', 1)[0]
  if scope not in _SCOPE_PREFIXES:
    raise UnsupportedScopeError(
        'Unsupported resource name [{}]: must start with one of {}.'.format(
            resource_name, ', '.join(sorted(_SCOPE_PREFIXES))
        )
    )
  return scope


class ComplianceClient(object):
  """Client for Data Boundary compliance resources in Assured Workloads API.

  Supports organization scoped parents for:
    - dbFrameworkComplianceSummaries.list
    - dbFindingSummaries.list
    - dbFrameworkComplianceReports.fetch / aggregate
    - dbFrameworkComplianceReports.dbControlComplianceSummaries.list
  """

  def __init__(self, release_track, no_http=False):
    """Initializes the client for the given release track.

    Args:
      release_track: base.ReleaseTrack, the release track of the command.
      no_http: bool, whether to create the API client without an HTTP object.
    """
    self.client = util.GetClientInstance(release_track, no_http=no_http)
    self.messages = util.GetMessagesModule(release_track)

  def _Service(self, scope, suffix):
    return getattr(self.client, '{}_locations_{}'.format(scope, suffix))

  def _Request(self, scope, suffix, **kwargs):
    request_class = getattr(
        self.messages,
        'Assuredworkloads{}Locations{}Request'.format(
            _SCOPE_PREFIXES[scope], suffix
        ),
    )
    return request_class(**kwargs)

  def _List(
      self,
      parent,
      service_suffix,
      request_suffix,
      field,
      limit,
      page_size,
      **kwargs
  ):
    """Pages through a scoped list method and yields the items in `field`."""
    scope = _GetScope(parent)
    request = self._Request(
        scope, request_suffix, parent=parent, pageSize=page_size, **kwargs
    )
    return list_pager.YieldFromList(
        self._Service(scope, service_suffix),
        request,
        field=field,
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def ListFrameworkComplianceSummaries(
      self, parent, view=None, limit=None, page_size=50
  ):
    """Lists Data Boundary framework compliance summaries.

    Args:
      parent: str, organizations/{ID}/locations/{LOCATION}.
      view: str or None, one of BASIC or FULL.
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch.

    Returns:
      A generator of framework compliance summaries.
    """
    kwargs = {}
    if view:
      request_class = getattr(
          self.messages,
          'Assuredworkloads{}LocationsDbFrameworkComplianceSummariesListRequest'
          .format(_SCOPE_PREFIXES[_GetScope(parent)]),
      )
      kwargs['view'] = request_class.ViewValueValuesEnum(
          'FRAMEWORK_COMPLIANCE_SUMMARY_VIEW_{}'.format(view.upper())
      )
    return self._List(
        parent,
        'dbFrameworkComplianceSummaries',
        'DbFrameworkComplianceSummariesList',
        'dbFrameworkComplianceSummaries',
        limit,
        page_size,
        **kwargs
    )

  def ListFindingSummaries(self, parent, limit=None, page_size=50):
    """Lists Data Boundary finding summaries.

    Args:
      parent: str, organizations/{ID}/locations/{LOCATION}.
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch.

    Returns:
      A generator of finding summaries.
    """
    return self._List(
        parent,
        'dbFindingSummaries',
        'DbFindingSummariesList',
        'dbFindingSummaries',
        limit,
        page_size,
    )

  def ListControlComplianceSummaries(self, parent, limit=None, page_size=50):
    """Lists control compliance summaries of a framework compliance report.

    Args:
      parent: str, the framework compliance report name, in the form
        organizations/{ID}/locations/{LOCATION}/
        dbFrameworkComplianceReports/{REPORT}.
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch.

    Returns:
      A generator of control compliance summaries.
    """
    return self._List(
        parent,
        'dbFrameworkComplianceReports_dbControlComplianceSummaries',
        'DbFrameworkComplianceReportsDbControlComplianceSummariesList',
        'dbControlComplianceSummaries',
        limit,
        page_size,
    )

  def FetchFrameworkComplianceReport(self, name):
    """Fetches the latest Data Boundary framework compliance report.

    Args:
      name: str, organizations/{ID}/locations/{LOCATION}/
        dbFrameworkComplianceReports/{REPORT}.

    Returns:
      The FetchDbFrameworkComplianceReportResponse message.
    """
    scope = _GetScope(name)
    request = self._Request(
        scope,
        'DbFrameworkComplianceReportsFetch',
        name=name,
    )
    return self._Service(scope, 'dbFrameworkComplianceReports').Fetch(request)

  def AggregateFrameworkComplianceReport(
      self, name, start_time=None, end_time=None
  ):
    """Aggregates a Data Boundary framework compliance report over time.

    Args:
      name: str, organizations/{ID}/locations/{LOCATION}/
        dbFrameworkComplianceReports/{REPORT}.
      start_time: str or None, RFC 3339 start of the aggregation interval.
      end_time: str or None, RFC 3339 end of the aggregation interval.

    Returns:
      The AggregateDbFrameworkComplianceReportResponse message.
    """
    scope = _GetScope(name)
    request = self._Request(
        scope,
        'DbFrameworkComplianceReportsAggregate',
        name=name,
        interval_startTime=start_time,
        interval_endTime=end_time,
    )
    return self._Service(scope, 'dbFrameworkComplianceReports').Aggregate(
        request
    )
