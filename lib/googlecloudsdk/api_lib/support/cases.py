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

import contextlib

from apitools.base.py.exceptions import HttpError

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

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

_SUPPORT_API_DISABLED_MSG = (
    'The Cloud Support API is not enabled in the project used for quota. '
    'Enable it there, or retry with `--billing-project=PROJECT` or '
    '`gcloud config set billing/quota_project PROJECT` to use a project '
    'where it is enabled.')


class CaseNotFoundError(core_exceptions.Error):
  """The requested Cloud Support case was not found."""


class CasePermissionDeniedError(core_exceptions.Error):
  """Permission was denied when accessing the Cloud Support case."""


class ServiceDisabledError(core_exceptions.Error):
  """The Cloud Support API is disabled in the project the call was billed to."""


@contextlib.contextmanager
def UserProjectQuotaWithFallback():
  """Temporarily enables user-project quota with fallback.

  gcloud reads billing/quota_project when a client or session is built, not per
  request, so wrapping only that construction scopes the mode to the Cloud
  Support transport. `gcloud compute` runs in legacy quota mode and the Cloud
  Support API is not enabled in gcloud's default client project, while the
  Resource Manager and Cloud Storage calls of the same command must keep the
  legacy mode. --billing-project, CLOUDSDK_BILLING_QUOTA_PROJECT and the
  billing/quota_project property still take precedence over this fallback.

  Yields:
    Nothing; the previous quota_project callbacks are restored on exit.
  """
  quota_project = properties.VALUES.billing.quota_project
  # Copy: ClearCallback() below empties the live list in place.
  saved_callbacks = list(quota_project.callbacks)
  base.EnableUserProjectQuotaWithFallback()
  try:
    yield
  finally:
    quota_project.ClearCallback()
    for callback in saved_callbacks:
      quota_project.AddCallback(callback)


def _IsServiceDisabled(http_error):
  """Returns True if an ErrorInfo detail has reason SERVICE_DISABLED.

  apis.CheckResponse already handles SERVICE_DISABLED bodies that name a
  project to enable the API in (it prompts or raises HttpException) before the
  error reaches GetCase; this catches the remaining shape, where the call
  reached the API without a usable quota project.

  Args:
    http_error: apitools HttpError, the 403 returned by the Cloud Support API.

  Returns:
    bool, True if the error carries an ErrorInfo with reason SERVICE_DISABLED.
  """
  payload = api_exceptions.HttpException(http_error).payload
  # type_details exists only when the body parsed as a JSON error; empty or
  # non-JSON 403 bodies carry no details.
  for detail in getattr(payload, 'type_details', {}).get('ErrorInfo', []):
    if detail.get('reason') == 'SERVICE_DISABLED':
      return True
  return False


def GetCase(case_name):
  """Gets a Cloud Support case by resource name.

  Args:
    case_name: str, the case resource name (projects/PROJECT/cases/CASE or
      organizations/ORG/cases/CASE).

  Returns:
    The Case resource message.

  Raises:
    CaseNotFoundError: if the case was not found (HTTP 404).
    ServiceDisabledError: if the Cloud Support API is disabled for the project
      the call was billed to and gcloud did not offer to enable it (HTTP 403
      SERVICE_DISABLED).
    CasePermissionDeniedError: if permission was denied (HTTP 403).
    HttpError: if any other HTTP error occurred.
  """
  with UserProjectQuotaWithFallback():
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
      if _IsServiceDisabled(e):
        log.debug('Cloud Support API returned SERVICE_DISABLED: %s', e.content)
        raise ServiceDisabledError(_SUPPORT_API_DISABLED_MSG) from e
      raise CasePermissionDeniedError(
          _SUPPORT_CASE_PERMISSION_MSG.format(case=case_name)
      ) from e
    raise


def IsClosed(case):
  """Returns True if the Cloud Support case is closed."""
  messages = apis.GetMessagesModule('cloudsupport', 'v2')
  return case.state == messages.Case.StateValueValuesEnum.CLOSED
