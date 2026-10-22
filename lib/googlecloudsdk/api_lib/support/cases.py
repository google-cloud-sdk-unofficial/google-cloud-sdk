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
"""Helper functions for interacting with Cloud Support cases."""

from apitools.base.py.exceptions import HttpError

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions as core_exceptions

_SUPPORT_CASE_PERMISSION_MSG = """\
Support case [{case}] was not found or you do not have permission to access it.
The Cloud Support API returns the same error for both, so check that:
- the case number is correct and the case was opened under this project (for
  cases opened under an organization, pass organizations/ORG/cases/CASE);
- you have roles/cloudsupport.techSupportEditor (permission
  cloudsupport.techCaseAttachments.create) on the case's parent - for
  organization cases the role must be granted on the organization or folder,
  not on the project;
- the Cloud Support API is enabled and the project has a paid support plan."""


class CaseNotFoundError(core_exceptions.Error):
  """The requested Cloud Support case was not found."""


class CasePermissionDeniedError(core_exceptions.Error):
  """Permission was denied when accessing the Cloud Support case."""


def GetCase(case_name):
  """Gets a Cloud Support case by resource name.

  Args:
    case_name: str, the case resource name (projects/PROJECT/cases/CASE or
      organizations/ORG/cases/CASE).

  Returns:
    The Case resource message.

  Raises:
    CaseNotFoundError: if the case was not found (HTTP 404).
    CasePermissionDeniedError: if permission was denied (HTTP 403).
    HttpError: if any other HTTP error occurred.
  """
  client = apis.GetClientInstance('cloudsupport', 'v2')
  messages = client.MESSAGES_MODULE
  try:
    return client.cases.Get(
        messages.CloudsupportCasesGetRequest(name=case_name))
  except HttpError as e:
    if e.status_code == 404:
      raise CaseNotFoundError(
          'Support case [{}] not found. Check the case number and the project '
          '(or organization) the case was opened under.'.format(case_name)
      ) from e
    if e.status_code == 403:
      raise CasePermissionDeniedError(
          _SUPPORT_CASE_PERMISSION_MSG.format(case=case_name)
      ) from e
    raise


def IsClosed(case):
  """Returns True if the Cloud Support case is closed."""
  messages = apis.GetMessagesModule('cloudsupport', 'v2')
  return case.state == messages.Case.StateValueValuesEnum.CLOSED
