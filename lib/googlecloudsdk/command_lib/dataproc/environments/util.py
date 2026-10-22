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
"""Utilities for gcloud dataproc environments commands."""

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import util as dataproc_util
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.generated_clients.apis.dataproc.v2 import dataproc_v2_messages


def ResolveBaseEnvironmentName(
    base_env: str | None, environment_ref: resources.Resource
) -> str | None:
  """Resolves a short base environment ID or returns a full resource name.

  Args:
    base_env: A base environment ID or full resource name, or None.
    environment_ref: The resource reference of the environment being created
      or updated. Its project and location are used to expand a short ID.

  Returns:
    The full resource name of the base environment, or None if `base_env` is
    empty.
  """
  if not base_env:
    return None
  if base_env.startswith('projects/'):
    return base_env
  return resources.REGISTRY.Parse(
      base_env,
      params={
          'projectsId': environment_ref.projectsId,
          'locationsId': environment_ref.locationsId,
      },
      collection='dataproc.projects.locations.environments',
      api_version=environment_ref.GetCollectionInfo().api_version,
  ).RelativeName()


_PYTHON_PACKAGE_HELP = (
    'Python package to install, specified as a PEP 508 requirement string '
    '(for example, `pandas>=2.0,<3`). Repeat this flag to install multiple '
    'packages.'
)

_PYTHON_PACKAGES_REPOSITORY_HELP = (
    'URI of a custom package repository to download the Python packages from '
    '(for example, `https://us-python.pkg.dev/my-project/my-repo/simple/`). '
    'If not specified, packages are downloaded from the public PyPI index.'
)


def AddCommonEnvironmentFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds common flags shared between create and update commands.

  Args:
    parser: The argparse parser to add the flags to.
  """
  parser.add_argument(
      '--description',
      help='Human-readable description of the environment.',
  )
  base_group = parser.add_mutually_exclusive_group()
  base_group.add_argument(
      '--base-version',
      help=(
          'Predefined base environment version to build upon '
          '(for example, `1.0`).'
      ),
  )
  base_group.add_argument(
      '--base-environment',
      help=(
          'ID or full resource name of an existing environment to build upon '
          '(`projects/PROJECT/locations/LOCATION/environments/ENVIRONMENT`).'
      ),
  )


def AddCreateEnvironmentFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds flags for `environments create`.

  Args:
    parser: The argparse parser to add the flags to.
  """
  AddCommonEnvironmentFlags(parser)
  parser.add_argument(
      '--python-package',
      action='append',
      metavar='PACKAGE',
      help=_PYTHON_PACKAGE_HELP,
  )
  parser.add_argument(
      '--python-packages-repository',
      metavar='URI',
      help=_PYTHON_PACKAGES_REPOSITORY_HELP,
  )
  labels_util.AddCreateLabelsFlags(parser)


def AddUpdateEnvironmentFlags(
    parser: parser_arguments.ArgumentInterceptor,
) -> None:
  """Adds flags for `environments update`.

  Args:
    parser: The argparse parser to add the flags to.
  """
  AddCommonEnvironmentFlags(parser)
  packages_group = parser.add_mutually_exclusive_group()
  packages_group.add_argument(
      '--python-package',
      action='append',
      metavar='PACKAGE',
      help=(
          _PYTHON_PACKAGE_HELP
          + ' The specified packages replace the existing package list.'
      ),
  )
  packages_group.add_argument(
      '--clear-python-packages',
      action='store_true',
      help='Clear all Python packages from the environment.',
  )
  repository_group = parser.add_mutually_exclusive_group()
  repository_group.add_argument(
      '--python-packages-repository',
      metavar='URI',
      help=(
          _PYTHON_PACKAGES_REPOSITORY_HELP
          + ' The specified repository replaces the existing one.'
      ),
  )
  repository_group.add_argument(
      '--clear-python-packages-repository',
      action='store_true',
      help=(
          'Remove the custom package repository from the environment, so that '
          'the Python packages are downloaded from the public PyPI index.'
      ),
  )
  labels_util.AddUpdateLabelsFlags(parser)


def _GetOrCreatePythonPackagesConfig(
    dataproc: dp.Dataproc, environment: dataproc_v2_messages.Environment
) -> dataproc_v2_messages.PythonPackagesConfig:
  """Returns the environment's `pythonPackagesConfig`, creating it if unset.

  Args:
    dataproc: The API wrapper, which must use the v2 API.
    environment: The environment being built.

  Returns:
    The `pythonPackagesConfig` message set on the environment.
  """
  if environment.pythonPackagesConfig is None:
    environment.pythonPackagesConfig = dataproc.messages.PythonPackagesConfig()
  return environment.pythonPackagesConfig


def BuildEnvironmentForCreate(
    dataproc: dp.Dataproc,
    args: parser_extensions.Namespace,
    environment_ref: resources.Resource,
) -> dataproc_v2_messages.Environment:
  """Builds an Environment message from parsed create flags.

  Args:
    dataproc: The API wrapper, which must use the v2 API.
    args: The parsed arguments of `environments create`.
    environment_ref: The resource reference of the environment to create.

  Returns:
    The environment to send in the create request.
  """
  messages = dataproc.messages
  environment = messages.Environment(name=environment_ref.RelativeName())

  if args.IsSpecified('description'):
    environment.description = args.description

  if args.IsSpecified('base_version'):
    environment.baseVersion = args.base_version
  elif args.IsSpecified('base_environment'):
    environment.baseEnvironment = ResolveBaseEnvironmentName(
        args.base_environment, environment_ref
    )

  if args.IsSpecified('python_package'):
    _GetOrCreatePythonPackagesConfig(dataproc, environment).packages = (
        args.python_package
    )
  if args.IsSpecified('python_packages_repository'):
    _GetOrCreatePythonPackagesConfig(dataproc, environment).repository = (
        messages.PackageRepository(uri=args.python_packages_repository)
    )

  environment.labels = labels_util.ParseCreateArgs(
      args, messages.Environment.LabelsValue
  )
  return environment


def BuildEnvironmentForUpdate(
    dataproc: dp.Dataproc,
    args: parser_extensions.Namespace,
    environment_ref: resources.Resource,
) -> tuple[dataproc_v2_messages.Environment, list[str]]:
  """Builds an Environment message and updateMask list from update flags.

  Args:
    dataproc: The API wrapper, which must use the v2 API.
    args: The parsed arguments of `environments update`.
    environment_ref: The resource reference of the environment to update.

  Returns:
    A tuple of the environment to send in the patch request and the list of
    changed field paths to use as the update mask.

  Raises:
    exceptions.ArgumentError: If no updatable field was specified.
  """
  messages = dataproc.messages
  environment = messages.Environment(name=environment_ref.RelativeName())
  changed_fields = []

  if args.IsSpecified('description'):
    environment.description = args.description
    changed_fields.append('description')

  if args.IsSpecified('base_version'):
    environment.baseVersion = args.base_version
    changed_fields.append('base_version')
  elif args.IsSpecified('base_environment'):
    environment.baseEnvironment = ResolveBaseEnvironmentName(
        args.base_environment, environment_ref
    )
    changed_fields.append('base_environment')

  if args.IsSpecified('python_package'):
    _GetOrCreatePythonPackagesConfig(dataproc, environment).packages = (
        args.python_package
    )
    changed_fields.append('python_packages_config.packages')
  elif args.clear_python_packages:
    _GetOrCreatePythonPackagesConfig(dataproc, environment).packages = []
    changed_fields.append('python_packages_config.packages')

  if args.IsSpecified('python_packages_repository'):
    _GetOrCreatePythonPackagesConfig(dataproc, environment).repository = (
        messages.PackageRepository(uri=args.python_packages_repository)
    )
    changed_fields.append('python_packages_config.repository')
  elif args.clear_python_packages_repository:
    # The field path in the mask with no repository set clears the repository.
    _GetOrCreatePythonPackagesConfig(dataproc, environment)
    changed_fields.append('python_packages_config.repository')

  def _GetCurrentLabels():
    get_request = messages.DataprocProjectsLocationsEnvironmentsGetRequest(
        name=environment_ref.RelativeName()
    )
    return dataproc.client.projects_locations_environments.Get(
        get_request
    ).labels

  labels_update = labels_util.ProcessUpdateArgsLazy(
      args,
      messages.Environment.LabelsValue,
      orig_labels_thunk=_GetCurrentLabels,
  )
  if labels_update.needs_update:
    environment.labels = labels_update.labels
    changed_fields.append('labels')

  if not changed_fields:
    raise exceptions.ArgumentError(
        'Must specify at least one environment parameter to update.'
    )

  return environment, changed_fields


def ReadEnvironment(
    dataproc: dp.Dataproc,
    source: str | None,
    environment_ref: resources.Resource,
) -> dataproc_v2_messages.Environment:
  """Reads an Environment message from a YAML file or standard input.

  A short `baseEnvironment` ID in the file is resolved to a full resource name
  in the project and location of `environment_ref`, as for `--base-environment`
  on `create` and `update`.

  Args:
    dataproc: The API wrapper, which must use the v2 API.
    source: The path of the YAML file to read, or None to read from standard
      input.
    environment_ref: The resource reference of the environment being imported.

  Returns:
    The environment parsed from the YAML data.

  Raises:
    exceptions.ParseError: If the YAML data cannot be parsed as an
      `Environment`.
    exceptions.ArgumentError: If the file sets both `baseVersion` and
      `baseEnvironment`.
  """
  data = console_io.ReadFromFileOrStdin(source or '-', binary=False)
  environment = export_util.Import(
      message_type=dataproc.messages.Environment, stream=data
  )
  if environment.baseVersion and environment.baseEnvironment:
    raise exceptions.ArgumentError(
        'Only one of `baseVersion` and `baseEnvironment` can be set in the'
        ' imported environment.'
    )
  if environment.baseEnvironment:
    environment.baseEnvironment = ResolveBaseEnvironmentName(
        environment.baseEnvironment, environment_ref
    )
  return environment


def GetImportUpdateMask(
    environment: dataproc_v2_messages.Environment,
) -> list[str]:
  """Returns the update mask to use when import overwrites an environment.

  The mask covers every user-settable field, so fields that are missing from
  the imported file are cleared. Of the `base_version` and `base_environment`
  oneof fields, only the one set in the file is included, because setting one
  of them clears the other. If the file sets neither, the base is unchanged.

  Args:
    environment: The environment read from the imported file.

  Returns:
    The list of field paths to use as the update mask.
  """
  update_mask = ['description']
  if environment.baseVersion:
    update_mask.append('base_version')
  elif environment.baseEnvironment:
    update_mask.append('base_environment')
  update_mask.extend([
      'python_packages_config.packages',
      'python_packages_config.repository',
      'labels',
  ])
  return update_mask


def WaitForEnvironmentOperation(
    dataproc: dp.Dataproc,
    operation: dataproc_v2_messages.Operation,
    environment_ref: resources.Resource,
    message: str,
    timeout_s: int,
) -> dataproc_v2_messages.Environment:
  """Waits for an Environment create/update LRO and returns the Environment.

  Args:
    dataproc: The API wrapper, which must use the v2 API.
    operation: The long-running operation returned by the create/update call.
    environment_ref: The resource reference of the environment.
    message: The message to display while waiting.
    timeout_s: The number of seconds to wait for the operation to complete.

  Returns:
    The environment fetched after the operation completes.

  Raises:
    OperationError: If the operation times out or finishes with an error.
  """
  dataproc_util.WaitForOperation(
      dataproc,
      operation,
      message=message,
      timeout_s=timeout_s,
  )
  get_request = (
      dataproc.messages.DataprocProjectsLocationsEnvironmentsGetRequest(
          name=environment_ref.RelativeName()
      )
  )
  return dataproc.client.projects_locations_environments.Get(get_request)


def CreateEnvironment(
    dataproc: dp.Dataproc,
    environment_ref: resources.Resource,
    environment: dataproc_v2_messages.Environment,
    args: parser_extensions.Namespace,
) -> dataproc_v2_messages.Operation | dataproc_v2_messages.Environment:
  """Creates an Environment and waits on the LRO unless `--async` is set.

  Args:
    dataproc: The API wrapper, which must use the v2 API.
    environment_ref: The resource reference of the environment to create.
    environment: The environment to create.
    args: The parsed command arguments; must have `async_` and `timeout`.

  Returns:
    The operation if `--async` is set, otherwise the created environment.
  """
  environment.name = environment_ref.RelativeName()
  request = (
      dataproc.messages.DataprocProjectsLocationsEnvironmentsCreateRequest(
          parent=environment_ref.Parent().RelativeName(),
          environmentId=environment_ref.Name(),
          environment=environment,
          requestId=dataproc_util.GetUniqueId(),
      )
  )
  operation = dataproc.client.projects_locations_environments.Create(request)
  if args.async_:
    log.status.Print(
        'Creating [{0}] with operation [{1}].'.format(
            environment_ref.RelativeName(), operation.name
        )
    )
    return operation
  result = WaitForEnvironmentOperation(
      dataproc,
      operation,
      environment_ref,
      message="Waiting for environment '{0}' creation operation".format(
          environment_ref.Name()
      ),
      timeout_s=args.timeout,
  )
  log.CreatedResource(environment_ref.RelativeName())
  return result


def UpdateEnvironment(
    dataproc: dp.Dataproc,
    environment_ref: resources.Resource,
    environment: dataproc_v2_messages.Environment,
    update_mask: list[str],
    args: parser_extensions.Namespace,
) -> dataproc_v2_messages.Operation | dataproc_v2_messages.Environment:
  """Updates an Environment and waits on the LRO unless `--async` is set.

  Args:
    dataproc: The API wrapper, which must use the v2 API.
    environment_ref: The resource reference of the environment to update.
    environment: The environment with the fields to update.
    update_mask: The list of field paths to update.
    args: The parsed command arguments; must have `async_` and `timeout`.

  Returns:
    The operation if `--async` is set, otherwise the updated environment.
  """
  environment.name = environment_ref.RelativeName()
  request = (
      dataproc.messages.DataprocProjectsLocationsEnvironmentsPatchRequest(
          name=environment_ref.RelativeName(),
          environment=environment,
          updateMask=','.join(update_mask),
          requestId=dataproc_util.GetUniqueId(),
      )
  )
  operation = dataproc.client.projects_locations_environments.Patch(request)
  if args.async_:
    log.status.Print(
        'Updating [{0}] with operation [{1}].'.format(
            environment_ref.RelativeName(), operation.name
        )
    )
    return operation
  result = WaitForEnvironmentOperation(
      dataproc,
      operation,
      environment_ref,
      message="Waiting for environment '{0}' update operation".format(
          environment_ref.Name()
      ),
      timeout_s=args.timeout,
  )
  log.UpdatedResource(environment_ref.RelativeName())
  return result
