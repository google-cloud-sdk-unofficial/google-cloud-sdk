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
"""Command to create SaaS Runtime Flags from a manifest file."""

from __future__ import annotations

import json
import pprint
from typing import Any, Callable
from apitools.base.protorpclite import messages as rpclite_messages
from apitools.base.py import encoding
from apitools.base.py import exceptions
import googlecloudsdk.api_lib.saasservicemgmt.util as saasservicemgmt_util
from googlecloudsdk.api_lib.util import messages as msg_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.saas_runtime import flags as arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.saasservicemgmt.v1beta1 import saasservicemgmt_v1beta1_client as ezclient
from googlecloudsdk.generated_clients.apis.saasservicemgmt.v1beta1 import saasservicemgmt_v1beta1_messages as ezmessages


FLAG_TYPE_MAP: dict[str, str] = {
    'boolean': 'FLAG_VALUE_TYPE_BOOL',
    'integer': 'FLAG_VALUE_TYPE_INT',
    'double': 'FLAG_VALUE_TYPE_DOUBLE',
    'string': 'FLAG_VALUE_TYPE_STRING',
}

VALUE_TYPE_HANDLERS: dict[str, tuple[str, type[Any]]] = {
    'FLAG_VALUE_TYPE_BOOL': ('booleanValue', bool),
    'FLAG_VALUE_TYPE_INT': ('integerValue', int),
    'FLAG_VALUE_TYPE_DOUBLE': ('doubleValue', float),
    'FLAG_VALUE_TYPE_STRING': ('stringValue', str),
}


def _ValidFlagType(flag_type: str | None) -> bool:
  """Returns True if the flag type is valid."""
  return flag_type is not None and flag_type in FLAG_TYPE_MAP


def _ParseFlagData(
    flag_key: str,
    unit_kind_name: str,
    flag_definition: dict[str, Any],
) -> dict[str, Any]:
  """Parses a flag definition and returns a dict of fields to be set."""
  log.debug(f'Flag definition:\n{pprint.pformat(flag_definition)}\n')

  flag_type = flag_definition.get('flagType')
  if not _ValidFlagType(flag_type):
    raise exceptions.InvalidDataError(
        f'Flag "{flag_key}" invalid. "{flag_type}" is not a supported flag'
        ' type.'
    )

  value_type = FLAG_TYPE_MAP.get(flag_type)

  default_value = flag_definition.get('defaultValue')
  if default_value is None:
    raise exceptions.InvalidDataError(
        f'Flag "{flag_key}" invalid. "defaultValue" is not set.'
    )

  default_evaluation_spec, default_variant = (
      _GetDefaultEvalSpecAndVariantsDicts(default_value, value_type)
  )

  flag_dict = {
      'key': flag_key,
      'valueType': value_type,
      'evaluationSpec': default_evaluation_spec,
      'variants': [default_variant],
      'unitKind': unit_kind_name,
  }
  if flag_definition.get('description'):
    flag_dict['description'] = flag_definition['description']

  return flag_dict


def _GetDefaultEvalSpecAndVariantsDicts(
    default_value: str, value_type: str
) -> tuple[dict[str, Any], dict[str, Any]]:
  """Returns the default evaluation spec and default variant for the given value type."""

  if value_type not in VALUE_TYPE_HANDLERS:
    raise exceptions.InvalidDataError(f'Unsupported value type: {value_type}')

  variant_type, expected_type = VALUE_TYPE_HANDLERS[
      value_type
  ]
  if not isinstance(default_value, expected_type):
    raise exceptions.InvalidDataError(
        f'Invalid default value "{default_value}" for type {value_type}.'
        f' Expected type {expected_type.__name__} but got'
        f' {type(default_value).__name__}.'
    )

  variant_dict = {
      'id': 'default',
  }
  variant_dict[variant_type] = expected_type(default_value)

  return {'defaultTarget': 'default'}, variant_dict


def _GetFlagMessagesFromManifest(
    manifest_json: dict[str, Any], unit_kind_name: str
) -> list[ezmessages.Flag]:
  """Parses a JSON manifest file and returns a list of flags."""

  if 'flags' not in manifest_json:
    raise exceptions.InvalidDataError(
        'Manifest must have a top-level "flags" key.'
    )

  flags_data = manifest_json['flags']
  if not isinstance(flags_data, dict):
    raise exceptions.InvalidDataError('"flags" property is invalid.')

  has_error = False
  flags = []
  for flag_key, flag_definition in flags_data.items():
    try:
      flag_dict = _ParseFlagData(flag_key, unit_kind_name, flag_definition)
      flag_msg = msg_utils.DictToMessageWithErrorCheck(
          flag_dict, ezmessages.Flag, throw_on_unexpected_fields=False
      )
      flags.append(flag_msg)
    except (
        rpclite_messages.ValidationError,
        exceptions.InvalidDataError,
    ) as e:
      log.error(f'Failed to parse flag definition for flag "{flag_key}": {e!r}')
      has_error = True

  if has_error:
    raise exceptions.InvalidDataError(
        'Failed to parse some flags in the manifest.'
    )

  return flags


def _GetValidFlags(
    flags: list[ezmessages.Flag],
    flags_service: ezclient.SaasservicemgmtV1beta1.ProjectsLocationsFlagsService,
    parent: str,
) -> list[ezmessages.Flag]:
  """Returns a list of flags that are valid to create."""
  valid_flags = []
  validation_failed = False
  for flag_msg in flags:
    try:
      _CreateFlag(flags_service, parent, flag_msg, validate_only=True)
    except exceptions.HttpConflictError:
      log.status.Print(f'Flag {flag_msg.key} already exists. Ignoring.')
    except exceptions.HttpError as e:
      _LogHttpError(e, flag_msg.key, log.error, 'Flag creation would fail')
      validation_failed = True
    except exceptions.InvalidDataError as e:
      log.error(f'Flag creation would fail: {e}')
      validation_failed = True
    else:
      valid_flags.append(flag_msg)

  if validation_failed:
    raise exceptions.InvalidDataError('Manifest file contains invalid flags')

  return valid_flags


def _IsFlagAlreadyExistsError(e: exceptions.HttpError) -> bool:
  """Returns True if the error is due to a flag already existing."""
  if not isinstance(e, exceptions.HttpError):
    return False

  if e.status_code != 400:
    return False

  try:
    error_content = json.loads(e.content)
    error_message = error_content.get('error', {}).get('message', '')
    return 'already exists' in error_message
  except json.JSONDecodeError:
    return False


def _GetExistingFlag(
    flags_service: ezclient.SaasservicemgmtV1beta1.ProjectsLocationsFlagsService,
    parent: str,
    flag_key: str,
) -> ezmessages.Flag | None:
  """Gets a flag by its key."""
  try:
    get_request = ezmessages.SaasservicemgmtProjectsLocationsFlagsGetRequest(
        name=f'{parent}/flags/{flag_key}'
    )
    return flags_service.Get(get_request)
  except exceptions.HttpError as e:
    _LogHttpError(e, flag_key, log.error, 'Failed to get existing flag')
    return None


def _CreateFlag(
    flags_service: ezclient.SaasservicemgmtV1beta1.ProjectsLocationsFlagsService,
    parent: str,
    flag_msg: ezmessages.Flag,
    validate_only: bool = False,
) -> None:
  """Creates a flag in the SaaS Runtime API."""
  flags_create_req = (
      ezmessages.SaasservicemgmtProjectsLocationsFlagsCreateRequest(
          parent=parent,
          flagId=flag_msg.key,
          validateOnly=validate_only,
          flag=flag_msg,
      )
  )
  flags_create_req_dict = encoding.MessageToDict(flags_create_req)
  if not validate_only:
    log.status.Print(
        f'\nAttempting to create flag:\n{pprint.pformat(flags_create_req_dict)}'
    )

  try:
    # Note: base_api client has a retry mechanism built in.
    flag_resp = flags_service.Create(flags_create_req)

    if not validate_only:
      log.status.Print(
          '\nCreated flag:\n'
          f'{pprint.pformat(encoding.MessageToDict(flag_resp))}'
      )

  except exceptions.HttpError as e:
    if _IsFlagAlreadyExistsError(e):
      existing_flag = _GetExistingFlag(flags_service, parent, flag_msg.key)
      if existing_flag is None:
        raise

      log.debug(
          f'\nFlag {flag_msg.key} already exists. Existing'
          f' flag:\n{pprint.pformat(encoding.MessageToDict(existing_flag))}'
      )

      if existing_flag.valueType != flag_msg.valueType:
        raise exceptions.InvalidDataError(
            f'Flag {flag_msg.key} of type {flag_msg.valueType} already exists'
            f' with different value type {existing_flag.valueType}'
        ) from e
      else:
        raise exceptions.HttpConflictError(
            e.response, e.content, e.url, e.method_config, e.request
        )
    else:
      raise e


def _LogHttpError(
    e: exceptions.HttpError,
    flag_key: str,
    log_func: Callable[[str], None],
    msg_prefix: str = '',
):
  """Logs an HTTP error."""
  try:
    error_content = json.loads(e.content)
    error_message = error_content.get('error', {}).get(
        'message', 'Unknown error'
    )
    error_code = error_content.get('error', {}).get('code', 'Unknown error')
    log_func(f'{msg_prefix} {flag_key}: {error_code} : {error_message}')
  except json.JSONDecodeError:
    log_func(f'{msg_prefix} {flag_key}: {e.content}')


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class Push(base.Command):
  """Create SaaS Runtime Flags from a JSON manifest file."""

  detailed_help = {
      'brief': 'Create Flags from a JSON manifest file.',
      'DESCRIPTION': """\
          Creates Flags based on the contents of a provided JSON manifest file. Flags defined in the file
          will be created. If a Flag already exists with the same type, it will be ignored. Otherwise,
          the command will exit with an error.
      """,
      'EXAMPLES': """\
          To create flags from a manifest file named `my_flags.json`:

              $ {command} --file=my_flags.json --unit-kind=my-unit-kind
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for gcloud saas-runtime flags push: --file, --unit-kind."""
    parser.add_argument(
        '--file',
        type=arg_parsers.FileContents(),
        required=True,
        help=(
            'Path to the JSON manifest file containing the flag definitions.'
            ' The manifest file must conform to the OpenFeature CLI flag'
            ' manifest schema.'
        ),
    )

    # This also implicitly adds the --location flag.
    arg_utils.AddUnitKindArgToParser(
        parser,
        required=True,
        help_text='UnitKind to push all the flags in the manifest file to.',
    )

  def Run(self, args):
    """Execute the gcloud saas-runtime flags push command."""

    project = properties.VALUES.core.project.Get()
    unit_kind_ref = args.CONCEPTS.unit_kind.Parse()
    parent = unit_kind_ref.Parent().RelativeName()

    log.debug(f'--project={project}')
    log.debug(f'--location={args.location}')
    log.debug(f'--unit-kind={args.unit_kind}')
    log.debug(f'Parent reference: {unit_kind_ref.Parent()}')
    log.debug(f'Parent relative name: {parent}')
    log.debug(f'UnitKind Name: {unit_kind_ref.Name()}')
    log.debug(f'UnitKind RelativeName: {unit_kind_ref.RelativeName()}')

    client = saasservicemgmt_util.GetV1Beta1ClientInstance()
    flags_service = client.projects_locations_flags

    # Parse the manifest file.
    try:
      manifest = json.loads(args.file)
    except json.JSONDecodeError as e:
      raise calliope_exceptions.ToolException(
          f'Failed to parse JSON: {e}'
      ) from e

    # Validate the manifest file.
    try:
      flags = _GetFlagMessagesFromManifest(
          manifest, unit_kind_ref.RelativeName()
      )
    except exceptions.InvalidDataError as e:
      raise calliope_exceptions.ToolException(
          f'Failed to parse flags: {e}'
      ) from e

    # Validate the flags.
    log.status.Print(f'Found {len(flags)} flags in manifest. Validating...')
    try:
      valid_flags = _GetValidFlags(flags, flags_service, parent)
    except exceptions.InvalidDataError as e:
      raise calliope_exceptions.ToolException(
          f'No flags were created: {e}'
      ) from e

    # Create the flags.
    if not valid_flags:
      log.status.Print('No valid flags to create. No flags were created.')
      return

    log.status.Print(
        'All flags validated successfully. Creating'
        f' {len(valid_flags)} flags...'
    )

    for flag_msg in valid_flags:
      try:
        _CreateFlag(flags_service, parent, flag_msg, validate_only=False)
      except exceptions.HttpError as e:
        _LogHttpError(e, flag_msg.key, log.error, 'Failed to create flag')
        raise calliope_exceptions.ToolException(
            f'Halting execution due to post-validation error: {e}'
        ) from e

    log.status.Print(f'{len(valid_flags)} flags created successfully.')
