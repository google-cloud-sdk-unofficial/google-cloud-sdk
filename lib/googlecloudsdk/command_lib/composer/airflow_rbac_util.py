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
"""Common utility functions for Composer Airflow RBAC commands."""

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import yaml

_MEMBER_KEY_TO_PREFIX = {
    'user': 'user:',
    'group': 'group:',
    'service_account': 'serviceAccount:',
    'principal': 'principal://',
}

_VALID_RBAC_MEMBER_PREFIXES = tuple(_MEMBER_KEY_TO_PREFIX.values())


def _ValidateRbacMemberPrefix(member):
  """Validates that member has a valid Airflow RBAC member prefix."""
  if not isinstance(member, str) or not member.startswith(
      _VALID_RBAC_MEMBER_PREFIXES
  ):
    raise command_util.InvalidUserInputError(
        "Invalid RBAC member '{}': members must be prefixed with 'group:',"
        " 'user:', 'serviceAccount:', or 'principal://'.".format(member)
    )


def ParseAirflowRbacConfigFile(
    file_path, release_track=base.ReleaseTrack.ALPHA
):
  """Parses a YAML or JSON file into an AirflowRbacConfig message.

  Args:
    file_path: str, path to local YAML/JSON file.
    release_track: base.ReleaseTrack, release track to determine messages
      module.

  Returns:
    AirflowRbacConfig message.

  Raises:
    command_util.InvalidUserInputError: if the file cannot be read or has an
      invalid RBAC configuration structure.
  """
  try:
    content = yaml.load_path(file_path)
  except yaml.Error as e:
    raise command_util.InvalidUserInputError(
        'Failed to read RBAC config file [{}]: {}'.format(file_path, e)
    ) from e

  if not isinstance(content, dict):
    raise command_util.InvalidUserInputError(
        'RBAC config file [{}] must contain a YAML/JSON object.'.format(
            file_path
        )
    )

  messages = api_util.GetMessagesModule(release_track=release_track)

  raw_bindings = content.get('bindings', [])
  if not isinstance(raw_bindings, list):
    raise command_util.InvalidUserInputError(
        "RBAC config 'bindings' must be a list of role bindings."
    )

  bindings = []
  for binding in raw_bindings:
    if not isinstance(binding, dict) or not binding.get('role'):
      raise command_util.InvalidUserInputError(
          'Each binding in RBAC config must be an object with a "role" and'
          ' "members" list.'
      )
    role = binding.get('role')
    members = binding.get('members', [])
    if not isinstance(members, list):
      raise command_util.InvalidUserInputError(
          "Members for role '{}' must be a list.".format(role)
      )
    for member in members:
      _ValidateRbacMemberPrefix(member)
    bindings.append(messages.AirflowRbacBinding(role=role, members=members))

  return messages.AirflowRbacConfig(bindings=bindings)


def ExtractMembersFromBindingDict(binding_dict):
  """Extracts role and members list from a single binding dict.

  Args:
    binding_dict: dict, keys may include 'role', 'user', 'group',
      'service_account', 'principal'.

  Returns:
    tuple of (role, members_list) where each member is prefixed with 'user:',
    'group:', 'serviceAccount:', or 'principal://'.

  Raises:
    command_util.InvalidUserInputError: if the binding dictionary is missing a
      role or valid members, or contains a mismatched member prefix.
  """
  if not isinstance(binding_dict, dict):
    raise command_util.InvalidUserInputError(
        'Invalid binding format. Expected a dictionary of key-value pairs.'
    )
  role = binding_dict.get('role')
  if not role:
    raise command_util.InvalidUserInputError(
        'Each binding must specify "role=ROLE".'
    )

  members = []
  for key, prefix in _MEMBER_KEY_TO_PREFIX.items():
    value = binding_dict.get(key)
    if value:
      value = value.strip()
      other_prefixes = tuple(
          p for p in _VALID_RBAC_MEMBER_PREFIXES if p != prefix
      )
      if value.startswith(other_prefixes):
        raise command_util.InvalidUserInputError(
            "Invalid {key} member '{value}': non-{prefix} prefix cannot be"
            " used in '{key}' field.".format(
                key=key, value=value, prefix=prefix.rstrip(':/')
            )
        )
      if not value.startswith(prefix):
        value = '{}{}'.format(prefix, value)
      members.append(value)

  if not members:
    raise command_util.InvalidUserInputError(
        "Binding for role '{}' must specify at least one member (user, group,"
        ' service_account, or principal).'.format(role)
    )

  return role, members


def ParseAirflowRbacBindingsList(
    bindings_list, release_track=base.ReleaseTrack.ALPHA
):
  """Parses a list of binding dicts into a list of AirflowRbacBinding messages.

  Args:
    bindings_list: list of dicts, each with 'role' and
      'user'/'group'/'service_account'/'principal'.
    release_track: base.ReleaseTrack, release track to determine messages
      module.

  Returns:
    list of AirflowRbacBinding messages.

  Raises:
    command_util.InvalidUserInputError: if any binding dict is invalid.
  """
  if not bindings_list:
    return []

  messages = api_util.GetMessagesModule(release_track=release_track)
  role_to_members = {}

  for binding_dict in bindings_list:
    role, members = ExtractMembersFromBindingDict(binding_dict)
    role_to_members.setdefault(role, set()).update(members)

  return [
      messages.AirflowRbacBinding(role=role, members=sorted(members))
      for role, members in sorted(role_to_members.items())
  ]


def ParseAirflowRbacConfig(
    airflow_rbac_binding=None,
    config_file=None,
    release_track=base.ReleaseTrack.ALPHA,
):
  """Constructs an AirflowRbacConfig message from create command arguments.

  Args:
    airflow_rbac_binding: list of dicts or None, repeated --airflow-rbac-binding
      flags.
    config_file: str or None, path to YAML/JSON config file.
    release_track: base.ReleaseTrack, release track.

  Returns:
    AirflowRbacConfig message or None.

  Raises:
    command_util.InvalidUserInputError: if both config_file and
      airflow_rbac_binding are specified, or if the RBAC configuration is
      invalid.
  """
  if config_file:
    if airflow_rbac_binding:
      raise command_util.InvalidUserInputError(
          'Cannot specify --airflow-rbac-config-from-file together with '
          '--airflow-rbac-binding.'
      )
    return ParseAirflowRbacConfigFile(config_file, release_track=release_track)

  if airflow_rbac_binding:
    messages = api_util.GetMessagesModule(release_track=release_track)
    bindings = ParseAirflowRbacBindingsList(
        airflow_rbac_binding, release_track=release_track
    )
    return messages.AirflowRbacConfig(bindings=bindings)

  return None


def ConstructAirflowRbacPatch(
    env_ref=None,
    env_obj=None,
    clear_airflow_rbac_config=None,
    update_airflow_rbac_binding=None,
    remove_airflow_rbac_binding=None,
    update_airflow_rbac_config_from_file=None,
    release_track=base.ReleaseTrack.ALPHA,
):
  """Constructs an environment patch for Airflow RBAC configuration.

  Args:
    env_ref: googlecloudsdk.core.resources.Resource, environment to patch.
    env_obj: messages.Environment, existing environment object if already
      fetched.
    clear_airflow_rbac_config: bool, whether to clear the entire RBAC config.
    update_airflow_rbac_binding: list of dicts, role-to-member bindings to add.
    remove_airflow_rbac_binding: list of dicts, role-to-member bindings to
      remove.
    update_airflow_rbac_config_from_file: str, path to YAML/JSON config file.
    release_track: base.ReleaseTrack, release track.

  Returns:
    (str, Environment) or (None, None).

  Raises:
    command_util.InvalidUserInputError: if mutually exclusive Airflow RBAC
      update flags are specified together or if the RBAC configuration is
      invalid.
  """
  messages = api_util.GetMessagesModule(release_track=release_track)

  has_file = bool(update_airflow_rbac_config_from_file)
  has_clear = bool(clear_airflow_rbac_config)
  has_binding_updates = bool(update_airflow_rbac_binding)
  has_binding_removes = bool(remove_airflow_rbac_binding)
  has_update = has_clear or has_binding_updates or has_binding_removes

  if not (has_file or has_update):
    return None, None

  if has_file and (has_clear or has_binding_updates or has_binding_removes):
    raise command_util.InvalidUserInputError(
        'Cannot specify --update-airflow-rbac-config-from-file together with'
        ' other Airflow RBAC flags.'
    )
  if has_clear and has_binding_removes:
    raise command_util.InvalidUserInputError(
        'Cannot specify --clear-airflow-rbac-config together with'
        ' --remove-airflow-rbac-binding.'
    )

  if has_file:
    rbac_config = ParseAirflowRbacConfigFile(
        update_airflow_rbac_config_from_file, release_track=release_track
    )
    patch_env = messages.Environment(
        config=messages.EnvironmentConfig(
            softwareConfig=messages.SoftwareConfig(
                airflowRbacConfig=rbac_config
            )
        )
    )
    return 'config.software_config.airflow_rbac_config', patch_env

  if has_clear and not has_binding_updates:
    return _ConstructClearAirflowRbacPatch(messages)

  if has_clear:
    existing_bindings = []
  else:
    if not env_obj and env_ref:
      env_obj = environments_api_util.Get(env_ref, release_track=release_track)

    current_rbac = None
    if env_obj and env_obj.config and env_obj.config.softwareConfig:
      current_rbac = env_obj.config.softwareConfig.airflowRbacConfig

    if current_rbac:
      existing_bindings = (
          list(current_rbac.bindings) if current_rbac.bindings else []
      )
    else:
      existing_bindings = []

  role_to_members = {}
  for binding in existing_bindings:
    role_to_members[binding.role] = set(binding.members)

  if remove_airflow_rbac_binding:
    for binding_dict in remove_airflow_rbac_binding:
      role, members = ExtractMembersFromBindingDict(binding_dict)
      if role in role_to_members:
        role_to_members[role].difference_update(members)

  if update_airflow_rbac_binding:
    for binding_dict in update_airflow_rbac_binding:
      role, members = ExtractMembersFromBindingDict(binding_dict)
      role_to_members.setdefault(role, set()).update(members)

  new_bindings = []
  for role, members in sorted(role_to_members.items()):
    sorted_members = sorted(members)
    if sorted_members:
      new_bindings.append(
          messages.AirflowRbacBinding(role=role, members=sorted_members)
      )

  if not new_bindings:
    return _ConstructClearAirflowRbacPatch(messages)

  rbac_config = messages.AirflowRbacConfig(
      bindings=new_bindings,
  )
  patch_env = messages.Environment(
      config=messages.EnvironmentConfig(
          softwareConfig=messages.SoftwareConfig(airflowRbacConfig=rbac_config)
      )
  )
  return 'config.software_config.airflow_rbac_config', patch_env


def _ConstructClearAirflowRbacPatch(messages):
  """Returns an environment patch that clears the Airflow RBAC configuration."""
  patch_env = messages.Environment(
      config=messages.EnvironmentConfig(
          softwareConfig=messages.SoftwareConfig(airflowRbacConfig=None)
      )
  )
  return 'config.software_config.airflow_rbac_config', patch_env
