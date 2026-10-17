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
"""Utilities for reCAPTCHA policies commands."""

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def AddKeyResourceArg(parser, verb):
  """Add a resource argument for a reCAPTCHA key."""
  resource_spec = concepts.ResourceSpec(
      'recaptchaenterprise.projects.keys',
      resource_name='key',
      keysId=concepts.ResourceParameterAttributeConfig(
          name='key', help_text='The ID of the reCAPTCHA key.'
      ),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=True,
  )

  concept_parsers.ConceptParser.ForResource(
      '--key',
      resource_spec,
      f'The reCAPTCHA key whose policy {verb}.',
      required=True,
  ).AddToParser(parser)


def GetDestructiveChanges(current_policy, new_policy):
  """Compares current and new policies and returns warning messages if changes are destructive."""
  if not current_policy:
    return []

  cleared_paths = []

  if _IsChallengeRuleGroupsCleared(
      current_policy.challengeRuleGroups,
      new_policy.challengeRuleGroups,
  ):
    cleared_paths.append('challenge_rule_groups')

  is_crg_replaced = _IsChallengeRuleGroupsReplaced(
      current_policy.challengeRuleGroups,
      new_policy.challengeRuleGroups,
  )

  cs_cleared, removed_items_by_path = _CheckClientSettingsChanges(
      current_policy.clientSettings,
      new_policy.clientSettings,
  )
  cleared_paths.extend(cs_cleared)

  return _FormatWarnings(cleared_paths, is_crg_replaced, removed_items_by_path)


def _IsChallengeRuleGroupsCleared(current_val, new_val):
  """Checks if challenge rule groups are cleared."""
  return bool(current_val and not new_val)


def _IsChallengeRuleGroupsReplaced(current_val, new_val):
  """Checks if challenge rule groups are replaced.

  Challenge rule groups are checked for full replacement rather than item-level
  removals because rule groups have complex nested conditions, priority
  ordering, and actions without a simple scalar key for diffing.

  Args:
    current_val: The current challengeRuleGroups list.
    new_val: The new challengeRuleGroups list.

  Returns:
    True if challenge rule groups are replaced, False otherwise.
  """
  return bool(current_val and new_val and current_val != new_val)


def _CheckClientSettingsChanges(current_cs, new_cs):
  """Checks client settings for cleared fields or removed items.

  Args:
    current_cs: The current clientSettings message.
    new_cs: The new clientSettings message.

  Returns:
    A tuple of (cleared_paths: list[str], removed_items_by_path: dict[str,
    list[str]]).
  """
  if not current_cs:
    return [], {}

  if not new_cs:
    return ['client_settings'], {}

  cleared_paths = []
  removed_items_by_path = {}

  # Check allowedDomains (track removals)
  is_cleared, removed = _CheckRepeatedFieldRemovals(
      current_cs.allowedDomains,
      new_cs.allowedDomains,
  )
  if is_cleared:
    cleared_paths.append('client_settings.allowed_domains')
  elif removed:
    removed_items_by_path['client_settings.allowed_domains'] = removed

  # Check protectedEndpoints (track path removals)
  current_pe = (
      current_cs.protectedEndpointGroup.protectedEndpoints
      if current_cs.protectedEndpointGroup
      else None
  )
  new_pe = (
      new_cs.protectedEndpointGroup.protectedEndpoints
      if new_cs.protectedEndpointGroup
      else None
  )
  pe_path = 'client_settings.protected_endpoint_group.protected_endpoints'
  is_cleared, removed = _CheckRepeatedFieldRemovals(
      current_pe,
      new_pe,
      key_fn=lambda x: x.path,
  )
  if is_cleared:
    cleared_paths.append(pe_path)
  elif removed:
    removed_items_by_path[pe_path] = removed

  return cleared_paths, removed_items_by_path


def _CheckRepeatedFieldRemovals(current_list, new_list, key_fn=None):
  """Checks if items were removed from a repeated field.

  Args:
    current_list: The current list of items.
    new_list: The new list of items.
    key_fn: Optional function to extract a comparable key from each item.

  Returns:
    A tuple of (is_cleared: bool, removed_items: list[str]).
  """
  if not current_list:
    return False, []

  if not new_list:
    return True, []

  if key_fn:
    current_keys = {key_fn(x) for x in current_list} - {None}
    new_keys = {key_fn(x) for x in new_list} - {None}
  else:
    current_keys = set(current_list)
    new_keys = set(new_list)

  removed = current_keys - new_keys
  return False, sorted(removed) if removed else []


def _FormatWarnings(cleared_paths, is_crg_replaced, removed_items_by_path):
  """Formats destructive change findings into user-facing warning strings."""
  warnings = []
  if cleared_paths:
    warnings.append(f'This operation will clear: {", ".join(cleared_paths)}.')
  if is_crg_replaced:
    warnings.append('This operation will replace: challenge_rule_groups.')
  for path, items in sorted(removed_items_by_path.items()):
    warnings.append(
        f'This operation will remove the following from {path}:'
        f' {", ".join(items)}.'
    )
  return warnings
