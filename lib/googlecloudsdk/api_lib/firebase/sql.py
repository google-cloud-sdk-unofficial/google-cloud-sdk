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
"""API client helper for Firebase SQL Connect management."""

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.firebase import util as firebase_util


def _FormatProjectName(project_id):
  """Formats project ID into full resource name."""
  if project_id.startswith('projects/'):
    return project_id
  return 'projects/{}'.format(project_id)


class SqlClient:
  """Client for Firebase SQL Connect API."""

  def __init__(self, client=None, messages=None):
    self.client = client or firebase_util.GetSqlClientInstance()
    self.messages = messages or firebase_util.GetSqlMessagesModule()

  def ListLocations(self, project_id, page_size=None):
    """Lists available Firebase SQL Connect locations for a project.

    Args:
      project_id: str, Google Cloud project ID or full resource name.
      page_size: int or None, number of items to request per page.

    Yields:
      Location message resources.
    """
    parent = _FormatProjectName(project_id)
    request = self.messages.FirebasedataconnectProjectsLocationsListRequest(
        name=parent
    )
    try:
      yield from list_pager.YieldFromList(
          service=self.client.projects_locations,
          request=request,
          batch_size=page_size,
          field='locations',
          batch_size_attribute='pageSize',
      )
    except apitools_exceptions.HttpError as e:
      firebase_util.HandleHttpError(e)
