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
"""API client interactions for IAM, Resource Manager, and Secret Manager."""

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.iam import util as iam_api_util
from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log
import six


def FindServiceAccountEmail(
    project, sa_name, iam_client=None, iam_messages=None
):
  """Finds a service account email matching `sa_name@*` in `project`."""
  if iam_client is None or iam_messages is None:
    iam_client, iam_messages = iam_api_util.GetClientAndMessages()
  prefix = '{}@'.format(sa_name)
  request = iam_messages.IamProjectsServiceAccountsListRequest(
      name=iam_util.ProjectToProjectResourceName(project)
  )
  for account in list_pager.YieldFromList(
      iam_client.projects_serviceAccounts,
      request,
      field='accounts',
      batch_size_attribute='pageSize',
  ):
    if account.email and account.email.startswith(prefix):
      return account.email
  return None


def CreateServiceAccount(
    project, sa_name, display_name, iam_client=None, iam_messages=None
):
  """Creates a service account in `project` and returns its resolved email."""
  if iam_client is None or iam_messages is None:
    iam_client, iam_messages = iam_api_util.GetClientAndMessages()
  created = iam_client.projects_serviceAccounts.Create(
      iam_messages.IamProjectsServiceAccountsCreateRequest(
          name=iam_util.ProjectToProjectResourceName(project),
          createServiceAccountRequest=(
              iam_messages.CreateServiceAccountRequest(
                  accountId=sa_name,
                  serviceAccount=iam_messages.ServiceAccount(
                      displayName=display_name
                  ),
              )
          ),
      )
  )
  return created.email or FindServiceAccountEmail(
      project, sa_name, iam_client=iam_client, iam_messages=iam_messages
  )


def GrantProjectRoles(project_ref, sa_email, roles):
  """Grants project-level IAM `roles` to `sa_email`."""
  member = 'serviceAccount:{}'.format(sa_email)
  for role in roles:
    log.status.Print('Granting {} to {}...'.format(role, sa_email))
    try:
      projects_api.AddIamPolicyBinding(project_ref, member, role)
    except apitools_exceptions.HttpError as err:
      log.warning(
          'Failed to grant %s to %s (%s). This may be expected if you do not'
          ' have IAM permissions on the project.',
          role,
          sa_email,
          err,
      )


def GrantServiceAccountUserRole(
    sa_email, member, iam_client=None, iam_messages=None
):
  """Grants `roles/iam.serviceAccountUser` on `sa_email` to `member`."""
  if iam_client is None or iam_messages is None:
    iam_client, iam_messages = iam_api_util.GetClientAndMessages()
  try:
    sa_resource = iam_util.EmailToAccountResourceName(sa_email)
    sa_policy = iam_client.projects_serviceAccounts.GetIamPolicy(
        iam_messages.IamProjectsServiceAccountsGetIamPolicyRequest(
            resource=sa_resource,
            options_requestedPolicyVersion=(
                iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
            ),
        )
    )
    sa_policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
    iam_util.AddBindingToIamPolicy(
        iam_messages.Binding,
        sa_policy,
        member,
        'roles/iam.serviceAccountUser',
    )
    iam_client.projects_serviceAccounts.SetIamPolicy(
        iam_messages.IamProjectsServiceAccountsSetIamPolicyRequest(
            resource=sa_resource,
            setIamPolicyRequest=iam_messages.SetIamPolicyRequest(
                policy=sa_policy
            ),
        )
    )
  except apitools_exceptions.HttpError as err:
    log.warning(
        'Failed to grant serviceAccountUser on %s (%s). You may need to'
        ' manually grant this to use the service account.',
        sa_email,
        err,
    )


def CreateOrUpdateSecret(
    secret_ref,
    region,
    payload_bytes,
    data_crc32c,
    labels=None,
    secrets_client=None,
):
  """Creates a Secret Manager secret if missing and adds a new version."""
  client = secrets_client or secrets_api.Secrets()
  existing = client.GetOrNone(secret_ref)
  if existing is None:
    log.status.Print(
        'Creating secret {} in {}...'.format(secret_ref.Name(), region)
    )
    labels_msg = None
    if labels:
      labels_msg = client.messages.Secret.LabelsValue(
          additionalProperties=[
              client.messages.Secret.LabelsValue.AdditionalProperty(
                  key=key, value=value
              )
              for key, value in sorted(six.iteritems(labels))
          ]
      )
    client.Create(
        secret_ref=secret_ref,
        policy='user-managed',
        locations=[region],
        labels=labels_msg,
        tags=None,
    )
  else:
    log.warning(
        'Secret %s already exists. Adding a new version.', secret_ref.Name()
    )

  log.status.Print('Adding version to secret {}...'.format(secret_ref.Name()))
  client.AddVersion(secret_ref, payload_bytes, data_crc32c)
