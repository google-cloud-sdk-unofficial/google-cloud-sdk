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
"""Command to create a local manifest file from the SaaS Flags API.

This command is used to create a local manifest file from the SaaS Flags API.
The manifest file will contain all flags for the specified UnitKind. By
default, the output file cannot already exist. Use `--overwrite-output-file`
to allow overwriting an existing file.
"""

from __future__ import annotations

from collections.abc import Iterable
import dataclasses
import json
import textwrap
from typing import Any, TypedDict

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
import googlecloudsdk.api_lib.saasservicemgmt.util as saasservicemgmt_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.saas_runtime import flags as arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.generated_clients.apis.saasservicemgmt.v1beta1 import saasservicemgmt_v1beta1_client as ezclient
from googlecloudsdk.generated_clients.apis.saasservicemgmt.v1beta1 import saasservicemgmt_v1beta1_messages as ezmessages

_OPENFEATURE_SCHEMA_URL = (
    'https://openfeature.dev/schemas/v1.0.0/flag-manifest.json'
)

_FlagValue = bool | int | float | str


# 1. Define required fields in a base TypedDict (total=True is default)
class _FlagDefinitionBase(TypedDict):
  """A set of flag properties in JSON manifest schema format.

  Attributes:
    flagType: The type of the flag (e.g., 'boolean', 'string').
    defaultValue: The default value of the flag.
  """
  flagType: str  # pylint: disable=invalid-name
  defaultValue: _FlagValue  # pylint: disable=invalid-name


class _FlagDefinition(_FlagDefinitionBase, total=False):
  """A set of flag properties in JSON manifest schema format.

  Attributes:
    flagType: The type of the flag (e.g., 'boolean', 'string').
    defaultValue: The default value of the flag.
    description: A human-readable description of the flag.
  """

  description: str  # pylint: disable=invalid-name


@dataclasses.dataclass(frozen=True, slots=True)
class _FlagTypeInfo:
  """A set of type-specific properties for a flag.

  Attributes:
    openfeature_type: The OpenFeature type name for the flag.
    default_value: The default value for this flag type.
  """

  openfeature_type: str
  default_value: _FlagValue


_FLAG_TYPE_INFO_BY_VALUE_TYPE: dict[
    ezmessages.Flag.ValueTypeValueValuesEnum, _FlagTypeInfo
] = {
    ezmessages.Flag.ValueTypeValueValuesEnum.FLAG_VALUE_TYPE_BOOL: (
        _FlagTypeInfo(
            openfeature_type='boolean',
            default_value=False,
        )
    ),
    ezmessages.Flag.ValueTypeValueValuesEnum.FLAG_VALUE_TYPE_INT: _FlagTypeInfo(
        openfeature_type='integer',
        default_value=0,
    ),
    ezmessages.Flag.ValueTypeValueValuesEnum.FLAG_VALUE_TYPE_DOUBLE: (
        _FlagTypeInfo(
            openfeature_type='double',
            default_value=0.0,
        )
    ),
    ezmessages.Flag.ValueTypeValueValuesEnum.FLAG_VALUE_TYPE_STRING: (
        _FlagTypeInfo(
            openfeature_type='string',
            default_value='',
        )
    ),
}


class InvalidFlagDataError(calliope_exceptions.ToolException):
  """Invalid or unsupported flag data from the API."""
  pass


def _GetFlagTypeInfo(
    flag_type: ezmessages.Flag.ValueTypeValueValuesEnum | None, flag_key: str
) -> _FlagTypeInfo:
  """Gets the type info or raises an error.

  Args:
    flag_type: The type enum from the API flag message.
    flag_key: The key of the flag (for error messages).

  Returns:
    The corresponding _FlagTypeInfo.

  Raises:
    InvalidFlagDataError: If the flag type is not supported.
  """
  if flag_type not in _FLAG_TYPE_INFO_BY_VALUE_TYPE:
    raise InvalidFlagDataError(
        f'Flag {flag_key!r} invalid. {flag_type} is not a supported'
        ' flag type.'
    )
  return _FLAG_TYPE_INFO_BY_VALUE_TYPE[flag_type]


def _ListFlagsIter(
    flags_service: ezclient.SaasservicemgmtV1beta1.ProjectsLocationsFlagsService,
    parent: str,
    *,
    flag_set: str | None = None,
) -> Iterable[ezmessages.Flag]:
  """Lists all flags for the given parent using automatic pagination.

  Args:
    flags_service: The SaaS Flags service client.
    parent: The parent resource name to list flags from.
    flag_set: The flag set ID to filter flags by.

  Yields:
    Flags from the API.

  Raises:
    ToolException: If the API call fails.
  """
  try:
    flags_iterator = list_pager.YieldFromList(
        service=flags_service,
        request=ezmessages.SaasservicemgmtProjectsLocationsFlagsListRequest(
            parent=parent,
        ),
        field='flags',
        batch_size_attribute='pageSize',
    )

    # TODO: b/479525288 - Replace with the filter parameter in the ListFlags
    # API call.
    yield from (
        f for f in flags_iterator
        if (flag_set is None or f.flagSet == flag_set)
    )
  except GeneratorExit:
    raise
  except apitools_exceptions.HttpError as e:
    raise calliope_exceptions.ToolException(
        f'Failed to retrieve flags for {parent!r} from the SaaS Flags API.'
    ) from e


def _ConstructFlagEntry(flag: ezmessages.Flag) -> _FlagDefinition:
  """Constructs a single flag entry for the manifest.

  Args:
    flag: The flag message from the API.

  Returns:
    A dictionary representing the flag definition in the manifest.
  """
  flag_type_info = _GetFlagTypeInfo(flag.valueType, flag.key)

  flag_definition: _FlagDefinition = {
      'flagType': flag_type_info.openfeature_type,
      'defaultValue': flag_type_info.default_value,
  }

  if flag.description:
    flag_definition['description'] = flag.description

  return flag_definition


def _ConstructManifest(flags: Iterable[ezmessages.Flag]) -> dict[str, Any]:
  """Constructs a JSON manifest file from an iterable of flags.

  Args:
    flags: An iterable of flag messages from the API.

  Returns:
    A dictionary representing the entire flag manifest.

  Raises:
    InvalidFlagDataError: If any flag data is invalid or duplicate.
  """
  manifest_flags = {}

  # All the flags are expected to be valid or we fail the entire command. We do
  # not want to write partial manifests files.
  for flag in flags:
    if not flag.key:
      raise InvalidFlagDataError(
          'Flag invalid. "key" is required but missing for flag name:'
          f' {flag.name!r}.'
      )

    if flag.key in manifest_flags:
      raise InvalidFlagDataError(
          f'Flag {flag.key!r} is a duplicate. '
          'Cannot create manifest with duplicate keys.'
      )

    # Errors are handled by InvalidFlagDataError propagation
    manifest_flags[flag.key] = _ConstructFlagEntry(flag)

  return {
      '$schema': _OPENFEATURE_SCHEMA_URL,
      'flags': manifest_flags,
  }


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class Pull(base.Command):
  """Command to create a JSON manifest file from the SaaS Flags API."""

  detailed_help = {
      'brief': (
          'Create a JSON manifest file using the SaaS Flags API as the source'
          ' of truth.'
      ),
      'DESCRIPTION': textwrap.dedent("""\
          Creates a Flags manifest file under the specified location. The manifest file will contain all
          flags for the specified UnitKind. By default, the output file cannot already exist. Use
          `--overwrite-output-file` to allow overwriting an existing file.
      """),
      'EXAMPLES': textwrap.dedent("""\
          To create a manifest file named `my_flags.json` in a home directory:

              $ {command} --output-file=~/my_flags.json --unit-kind=my-unit-kind
          """),
  }

  @staticmethod
  def Args(parser):
    """Registers flags for gcloud saas-runtime flags pull: --output-file, --unit-kind.

    Args:
      parser: The argparse parser.
    """
    parser.add_argument(
        '--output-file',
        type=str,
        required=True,
        help=(
            'Path to the JSON manifest file that will be created containing the'
            ' flag definitions. The manifest file will conform to the'
            ' OpenFeature CLI flag manifest schema.'
        ),
    )

    parser.add_argument(
        '--overwrite-output-file',
        action='store_true',
        default=False,
        help=(
            'Overwrite the output file if it already exists. Default is False.'
        ),
    )

    parser.add_argument(
        '--flag-set',
        type=str,
        required=False,
        help='Flag set ID to filter flags by.',
    )

    # This also implicitly adds the --location flag.
    arg_utils.AddUnitKindArgToParser(
        parser,
        required=True,
        help_text='UnitKind to pull all the flags from.',
    )

  def Run(self, args):
    """Executes the gcloud saas-runtime flags pull command.

    Args:
      args: An argparse namespace. All the arguments the command is called with.

    Raises:
      ToolException: If file writing fails or API call fails.
    """
    project = properties.VALUES.core.project.Get(required=True)
    unit_kind_ref = args.CONCEPTS.unit_kind.Parse()
    parent = unit_kind_ref.Parent().RelativeName()

    log.debug('--project=%s', project)
    log.debug('--location=%s', args.location)
    log.debug('--unit-kind=%s', args.unit_kind)
    log.debug('Parent reference: %s', unit_kind_ref.Parent())
    log.debug('Parent relative name: %s', parent)
    log.debug('UnitKind Name: %s', unit_kind_ref.Name())
    log.debug('UnitKind RelativeName: %s', unit_kind_ref.RelativeName())

    client = saasservicemgmt_util.GetV1Beta1ClientInstance()
    flags_service = client.projects_locations_flags

    log.status.Print(f'Fetching flags from {parent!r}...')
    flags_iterator = _ListFlagsIter(
        flags_service, parent, flag_set=args.flag_set
    )
    manifest_data = _ConstructManifest(flags_iterator)

    if not manifest_data.get('flags'):
      log.status.Print(
          f'No flags found or processed for {parent!r}. No manifest file was'
          ' created.'
      )
      return

    log.status.Print(
        'Generating manifest. Using zero values as defaultValue for all flags.'
    )
    manifest_content = json.dumps(
        manifest_data, indent=2, sort_keys=True, ensure_ascii=False
    )
    log.debug(
        'Manifest generated with %d flags.', len(manifest_data.get('flags', []))
    )

    try:
      files.WriteFileContents(
          path=args.output_file,
          contents=manifest_content,
          overwrite=args.overwrite_output_file,
      )
      log.status.Print(
          f'Successfully created manifest file at {args.output_file!r}'
      )
    except files.Error as e:
      raise calliope_exceptions.ToolException(
          f'Could not write to output file {args.output_file!r}'
      ) from e
