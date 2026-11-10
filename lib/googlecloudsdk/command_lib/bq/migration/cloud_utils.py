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
"""Shared cloud execution CLI orchestration utilities for BQ migration tools."""

import time

from googlecloudsdk.api_lib.bq.migration import cloud_utils as cloud_utils_api
from googlecloudsdk.command_lib.projects import util as projects_command_util
from googlecloudsdk.command_lib.util import crc32c
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
import six

IAM_PROPAGATION_SLEEP_SECONDS = 30


class ServiceAccountSetupError(exceptions.Error):
  """Raised when a dedicated service account cannot be found or created."""


def _FormatIamMember(identity):
  """Formats an identity email as a `user:` or `serviceAccount:` IAM member."""
  if ':' in identity:
    return identity
  prefix = (
      'serviceAccount:'
      if identity.endswith('.gserviceaccount.com')
      else 'user:'
  )
  return '{}{}'.format(prefix, identity)


def SetupServiceAccount(
    project,
    default_sa_name,
    default_sa_display_name,
    roles,
    service_account=None,
    service_account_user=None,
    sleep_fn=time.sleep,
):
  """Resolves or creates a dedicated service account and IAM bindings.

  Args:
    project: str, The GCP project ID.
    default_sa_name: str, Account ID of the dedicated service account to find or
      create when `service_account` is not specified.
    default_sa_display_name: str, Display name used when creating the dedicated
      service account.
    roles: Sequence[str], Project-level IAM roles to grant to the dedicated
      service account.
    service_account: str or None, Explicit service account email (or `'none'` to
      skip using a service account and return `''`).
    service_account_user: str or None, Explicit user email to grant
      `roles/iam.serviceAccountUser` on the dedicated service account (defaults
      to the active `core/account` property).
    sleep_fn: callable, Sleep function (`time.sleep`) for IAM propagation wait.

  Returns:
    str, The resolved service account email (or `''` if `service_account` is
    `'none'`).

  Raises:
    ServiceAccountSetupError: If the dedicated service account cannot be found
      or created.
  """
  if service_account == 'none':
    return ''
  if service_account:
    log.status.Print(
        'Using provided service account: {}'.format(service_account)
    )
    return service_account

  sa_email = cloud_utils_api.FindServiceAccountEmail(project, default_sa_name)
  if not sa_email:
    console_io.PromptContinue(
        message=(
            'Dedicated service account {} does not exist in project {}.'.format(
                default_sa_name, project
            )
        ),
        prompt_string=(
            'Do you want to create it and grant necessary permissions?'
        ),
        cancel_on_no=True,
    )
    log.status.Print(
        'Creating dedicated service account {}...'.format(default_sa_name)
    )
    sa_email = cloud_utils_api.CreateServiceAccount(
        project, default_sa_name, default_sa_display_name
    )

  if not sa_email:
    raise ServiceAccountSetupError(
        'Could not find or create service account {} in project {}.'.format(
            default_sa_name, project
        )
    )

  log.status.Print('Service account {} identified.'.format(sa_email))

  project_ref = projects_command_util.ParseProject(project)
  cloud_utils_api.GrantProjectRoles(project_ref, sa_email, roles)

  log.status.Print('Sleeping 30s for IAM propagation...')
  sleep_fn(IAM_PROPAGATION_SLEEP_SECONDS)

  identity = service_account_user or properties.VALUES.core.account.Get()
  if identity:
    log.status.Print(
        'Granting roles/iam.serviceAccountUser to {} on {}...'.format(
            identity, sa_email
        )
    )
    cloud_utils_api.GrantServiceAccountUserRole(
        sa_email, _FormatIamMember(identity)
    )
  else:
    log.warning(
        'Could not detect active account identity. You may need to manually'
        ' grant roles/iam.serviceAccountUser on %s.',
        sa_email,
    )

  return sa_email


def SetupSecretManager(
    project,
    region,
    payload,
    secret_ref=None,
    default_secret_id=None,
    labels=None,
):
  """Creates or updates a Secret Manager secret and adds a new version.

  Args:
    project: str, The GCP project ID.
    region: str, The replica region for user-managed secret replication.
    payload: str or bytes, The secret payload to store in the new version.
    secret_ref: resources.Resource or None, Parsed `--secret` resource reference
      if specified on the command line.
    default_secret_id: str or None, Secret ID to parse in `project` when
      `secret_ref` is None.
    labels: dict[str, str] or None, Optional labels to attach when creating a
      new secret.

  Returns:
    str, The short secret ID (`secret_ref.Name()`).

  Raises:
    ValueError: If both `secret_ref` and `default_secret_id` are None/empty.
  """
  if secret_ref is None:
    if not default_secret_id:
      raise ValueError(
          'Either secret_ref or default_secret_id must be provided.'
      )
    secret_ref = resources.REGISTRY.Parse(
        default_secret_id,
        params={'projectsId': project},
        collection='secretmanager.projects.secrets',
    )

  payload_bytes = six.ensure_binary(payload or '')
  data_crc32c = crc32c.get_checksum(crc32c.get_crc32c(payload_bytes))

  cloud_utils_api.CreateOrUpdateSecret(
      secret_ref=secret_ref,
      region=region,
      payload_bytes=payload_bytes,
      data_crc32c=data_crc32c,
      labels=labels,
  )
  return secret_ref.Name()
