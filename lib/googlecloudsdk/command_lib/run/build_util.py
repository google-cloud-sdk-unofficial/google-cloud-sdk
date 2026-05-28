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
"""Build utils."""

import os.path
import re

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.iam import util as iam_api_util
from googlecloudsdk.api_lib.run import service as service_lib
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.core import log

_LEGACY_BUILD_SA_FORMAT = r'^\d+@cloudbuild\.gserviceaccount\.com$'
_PROJECT_TOML_FILE_NAME = 'project.toml'


def _GetDefaultBuildServiceAccount(project_id, region='global'):
  """Gets the default build service account for a project."""
  client = cloudbuild_util.GetClientInstance(location=region)
  name = f'projects/{project_id}/locations/{region}/defaultServiceAccount'
  return client.projects_locations.GetDefaultServiceAccount(
      client.MESSAGES_MODULE.CloudbuildProjectsLocationsGetDefaultServiceAccountRequest(
          name=name
      )
  ).serviceAccountEmail


def _ExtractServiceAccountEmail(service_account):
  """Extracts the service account email from the service account resource."""
  match = re.search(r'/serviceAccounts/([^/]+)$', service_account)
  if match:
    return match.group(1)
  else:
    return None


def _DescribeServiceAccount(service_account_email):
  client, messages = iam_api_util.GetClientAndMessages()
  return client.projects_serviceAccounts.Get(
      messages.IamProjectsServiceAccountsGetRequest(
          name=iam_util.EmailToAccountResourceName(service_account_email)
      )
  )


def ValidateBuildServiceAccountAndPromptWarning(
    project_id, region, build_service_account=None
):
  """Util to validate the default build service account permission.

  Prompt a warning to users if cloudbuild.builds.builder is missing.

  Args:
    project_id: id of project.
    region: region to deploy the service.
    build_service_account: user provided build service account. It will be None,
      if user doesn't provide it.

  Raises:
    ServiceAccountError: if the build service account is disabled/not
    found/missing required permissions.
  """

  if build_service_account is None:
    build_service_account = _GetDefaultBuildServiceAccount(project_id, region)
  service_account_email = _ExtractServiceAccountEmail(build_service_account)

  try:
    if not re.match(_LEGACY_BUILD_SA_FORMAT, service_account_email):
      build_service_account_description = _DescribeServiceAccount(
          service_account_email
      )
      if build_service_account_description.disabled:
        raise serverless_exceptions.ServiceAccountError(
            'Could not build the function due to disabled service account used'
            ' by Cloud Build. Please make sure that the service account:'
            f' [{build_service_account}] is active.'
        )
  except apitools_exceptions.HttpForbiddenError:
    # Just show a warning but not breaking the deployment.
    # We are doing best effort here.
    log.warning(
        'Your account does not have permission to check details of build'
        f' service account {build_service_account}. If the deployment fails,'
        f' please ensure {build_service_account} is active.'
    )
  except apitools_exceptions.HttpNotFoundError as exc:
    log.warning(
        f'The build service account {build_service_account} does not exist. If'
        ' you just created this account, or if this is your first time'
        ' deploying with the default build service account, it may take a few'
        ' minutes for the service account to become fully available. Please'
        ' try again later.'
    )
    raise serverless_exceptions.ServiceAccountError(
        f'Build service account {build_service_account} does not exist.'
    ) from exc


def CreateBuildPack(container):
  """A helper method to configure buildpack."""
  pack = [{'image': container.image}]
  changes = []
  source = container.source
  project_toml_file = source + '/' + _PROJECT_TOML_FILE_NAME
  command_arg = getattr(container, 'command', None)
  function_arg = getattr(container, 'function', None)
  if command_arg is not None:
    command = ' '.join(command_arg)
    pack[0].update(
        {'envs': ['GOOGLE_ENTRYPOINT="{command}"'.format(command=command)]}
    )
  elif function_arg is not None:
    pack[0].update({
        'envs': [
            'GOOGLE_FUNCTION_SIGNATURE_TYPE=http',
            'GOOGLE_FUNCTION_TARGET={target}'.format(target=function_arg),
        ]
    })
  if os.path.exists(project_toml_file):
    pack[0].update({'project_descriptor': _PROJECT_TOML_FILE_NAME})
  return pack, changes


def GetBuildWorkerPool(args, annotated_build_worker_pool, service, changes):
  """Gets the build worker pool from user flags and annotations.

  Args:
    args: argparse.Namespace, Command line arguments
    annotated_build_worker_pool: Build worker pool value from service
      annotations.
    service: Existing Cloud Run service.
    changes: List of config changes.

  Returns:
    build_worker_pool value or
    None meaning clear-worker-pool flag was set
    or build-worker-pool was an empty string.
  """
  if _ShouldClearBuildWorkerPool(args):
    worker_pool_key = service_lib.RUN_FUNCTIONS_BUILD_WORKER_POOL_ANNOTATION
    if service and service.annotations.get(worker_pool_key):
      changes.append(config_changes.DeleteAnnotationChange(worker_pool_key))
    return None
  return (
      args.build_worker_pool
      if flags.FlagIsExplicitlySet(args, 'build_worker_pool')
      else annotated_build_worker_pool
  )


def _ShouldClearBuildWorkerPool(args):
  return flags.FlagIsExplicitlySet(args, 'clear_build_worker_pool') or (
      flags.FlagIsExplicitlySet(args, 'build_worker_pool')
      and not args.build_worker_pool
  )


def GetBuildServiceAccount(
    args, annotated_build_service_account, container, service, changes
):
  """Returns cloud build service account.

  Args:
    args: argparse.Namespace, Command line arguments
    annotated_build_service_account: string. The build service account annotated
      on the service used by cloud run functions.
    container: Container. The container to deploy.
    service: Service. The service being changed.
    changes: List of config changes.

  Returns:
    build service account value where
    None means there were no annotations, user specified to clear the
    build service account, or the build service account was an empty string.
  """
  build_sa_key = service_lib.RUN_FUNCTIONS_BUILD_SERVICE_ACCOUNT_ANNOTATION
  build_service_account = getattr(container, 'build_service_account', None)
  if _ShouldClearBuildServiceAccount(args, build_service_account):
    if service and service.annotations.get(build_sa_key):
      changes.append(config_changes.DeleteAnnotationChange(build_sa_key))
    return None
  return build_service_account or annotated_build_service_account


def _ShouldClearBuildServiceAccount(args, build_service_account):
  if flags.FlagIsExplicitlySet(args, 'clear_build_service_account'):
    return True
  if (
      flags.FlagIsExplicitlySet(args, 'build_service_account')
      and not build_service_account
  ):
    return True
  return False

