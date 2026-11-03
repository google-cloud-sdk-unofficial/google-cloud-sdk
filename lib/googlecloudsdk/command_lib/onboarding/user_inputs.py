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
"""Helper for handling user input for onboarding gcloud commands."""

from __future__ import annotations

from collections.abc import Sequence
import dataclasses
from typing import TYPE_CHECKING

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.onboarding import exceptions as onboarding_exceptions
from googlecloudsdk.command_lib.onboarding import telemetry
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

if TYPE_CHECKING:
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.generated_clients.apis.useronboarding.v1alpha import useronboarding_v1alpha_messages as onboarding_messages

CLOUD_TOS_ID = 'cloud'
STARTER_TIER_TOS_ID = 'starter-tier-additional-terms-of-service'
PANTHEON_TOS_ID = 'pantheon'
FREE_TRIAL_TOS_ID = 'cloud-free-trial'
GMP_DEMO_API_KEY_TOS_ID = 'gmp-demo-api-key'
FIREBASE_TOS_ID = 'firebase'

_TOS_HEADER = (
    'To provision resources on the starter tier, review and accept the terms of'
    ' service:'
)
_DECLINED_TOS_ERROR_HEADER = (
    'Terms of Service declined. Onboarding cannot proceed.'
)
_SOUTH_KOREA_COMMERCIAL_USE_NOTICE = (
    'If you are located in South Korea, you certify that you are using Google'
    ' Cloud Platform services solely for commercial purposes.'
)


@dataclasses.dataclass(frozen=True)
class _ToSInfo:
  title: str
  url: str


_STARTER_TIER_TOS = _ToSInfo(
    title='Google Cloud Starter Tier Additional Terms of Service',
    url='https://cloud.google.com/terms/starter-tier-additional-terms-of-service',
)

_TOS_REGISTRY: dict[str, _ToSInfo] = {
    CLOUD_TOS_ID: _ToSInfo(
        title='Google Cloud Terms of Service',
        url='https://cloud.google.com/terms',
    ),
    STARTER_TIER_TOS_ID: _STARTER_TIER_TOS,
    PANTHEON_TOS_ID: _ToSInfo(
        title='Google APIs Terms of Service',
        url='https://developers.google.com/terms/',
    ),
    FREE_TRIAL_TOS_ID: _ToSInfo(
        title='Google Cloud Free Trial Terms of Service',
        url='https://cloud.google.com/terms/free-trial',
    ),
    GMP_DEMO_API_KEY_TOS_ID: _ToSInfo(
        title='Google Maps Platform Demo API Key Terms of Service',
        url='https://cloud.google.com/terms/maps-platform/demo-project-terms',
    ),
    FIREBASE_TOS_ID: _ToSInfo(
        title='Firebase Terms of Service',
        url='https://firebase.google.com/terms',
    ),
}

VALID_TOS_IDS = tuple(_TOS_REGISTRY)

# Flag used to select a Google Cloud region without prompting.
REGION_FLAG = '--region'


def _FormatMessage(tos_list: list[_ToSInfo]) -> str:
  """Formats the terms of service message."""
  if len(tos_list) == 1:
    items = [f'• {tos_list[0].title} ({tos_list[0].url})']
  else:
    items = [
        f'{i}. {tos.title} ({tos.url})' for i, tos in enumerate(tos_list, 1)
    ]
  return '\n'.join(
      [_TOS_HEADER] + items + ['', _SOUTH_KOREA_COMMERCIAL_USE_NOTICE]
  )


class InvalidTosIdError(onboarding_exceptions.OnboardingError, ValueError):
  """Raised when one or more invalid Terms of Service IDs are provided."""


class UnsupportedTosIdError(onboarding_exceptions.OnboardingError):
  """Raised when the server requires ToS IDs unknown to this gcloud version."""


def GetUnsupportedTosIds(tos_ids: Sequence[str]) -> list[str]:
  """Returns the deduplicated `tos_ids` not recognized by this gcloud version."""
  return list(
      dict.fromkeys(tos_id for tos_id in tos_ids if tos_id not in _TOS_REGISTRY)
  )


def FormatUnsupportedToSError(unsupported_ids: Sequence[str]) -> str:
  """Formats the error for server-required ToS IDs unknown to this gcloud."""
  unsupported_str = ', '.join(unsupported_ids)
  return (
      'The server requires Terms of Service not supported by this gcloud'
      f' version: [{unsupported_str}]. Run `gcloud components update` and'
      ' retry.'
  )


def ValidateTosIds(tos_ids: Sequence[str]) -> None:
  """Validates that all provided ToS IDs are recognized.

  Args:
    tos_ids: Sequence of ToS IDs to validate.

  Raises:
    InvalidTosIdError: If any ToS ID is not in `VALID_TOS_IDS`.
  """
  invalid_ids = GetUnsupportedTosIds(tos_ids)
  if invalid_ids:
    invalid_str = ', '.join(invalid_ids)
    valid_str = ', '.join(VALID_TOS_IDS)
    raise InvalidTosIdError(
        f'Invalid Terms of Service ID(s): [{invalid_str}]. Update the command'
        f' to use valid --auto-accept-tos-ids values: {valid_str}.'
    )


def FormatDeclinedToSError(tos_ids: Sequence[str]) -> str:
  """Formats the error message when required Terms of Service are not accepted.

  Includes the required Terms of Service titles, URLs, and IDs, along with the
  `--auto-accept-tos-ids` flag needed to accept them non-interactively. If the
  server requires a Terms of Service ID this gcloud version does not recognize,
  acceptance cannot succeed, so the message instructs upgrading gcloud instead.

  Args:
    tos_ids: Sequence of required TOS IDs for the session.

  Returns:
    The formatted error message string.
  """
  unrecognized_ids = GetUnsupportedTosIds(tos_ids)
  if unrecognized_ids:
    return '\n'.join([
        _DECLINED_TOS_ERROR_HEADER,
        FormatUnsupportedToSError(unrecognized_ids),
    ])

  recognized_ids = [
      tos_id for tos_id in VALID_TOS_IDS if tos_id in set(tos_ids)
  ]
  if not recognized_ids:
    return _DECLINED_TOS_ERROR_HEADER

  if len(recognized_ids) == 1:
    tos_id = recognized_ids[0]
    tos = _TOS_REGISTRY[tos_id]
    items = [f'• {tos.title} ({tos.url}) [id: {tos_id}]']
  else:
    items = [
        f'{i}. {_TOS_REGISTRY[tos_id].title} ({_TOS_REGISTRY[tos_id].url})'
        f' [id: {tos_id}]'
        for i, tos_id in enumerate(recognized_ids, 1)
    ]

  flag_value = ','.join(recognized_ids)
  footer = (
      'To accept these Terms of Service non-interactively, re-run with'
      f' --auto-accept-tos-ids={flag_value}.'
  )
  return '\n'.join(
      [_DECLINED_TOS_ERROR_HEADER, _TOS_HEADER]
      + items
      + ['', _SOUTH_KOREA_COMMERCIAL_USE_NOTICE, '', footer]
  )


def _FormatPromptString(titles: list[str]) -> str:
  """Formats the prompt question asking for user acceptance."""
  if not titles:
    return ''
  if len(titles) == 1:
    return f'Do you accept the {titles[0]}?'
  if len(titles) == 2:
    return f'Do you accept the {titles[0]} and the {titles[1]}?'
  first_part = ', '.join(f'the {t}' for t in titles[:-1])
  return f'Do you accept {first_part}, and the {titles[-1]}?'


_TOS_MESSAGE = _FormatMessage([_STARTER_TIER_TOS])
_TOS_PROMPT = _FormatPromptString([_STARTER_TIER_TOS.title])

_REGION_MESSAGE = (
    'Please select the region where resources (Cloud Run, Firebase, CloudSQL)'
    ' associated with your project will be provisioned in:\n'
)
_SINGLE_CLOUD_REGION_MESSAGE = 'One region found and selected: [{region}].'
_AVAILABLE_CLOUD_REGIONS_MESSAGE = 'Available regions:'
_SUGGESTED_CLOUD_REGION_SUFFIX = ' [suggested]'
_CLOUD_REGION_REQUIRED_MESSAGE = (
    'A region must be selected to continue, but prompting is disabled. Rerun'
    ' the command with [{flag}=REGION].\n{available_message}\n{available}'
)
_UNSUPPORTED_CLOUD_REGION_MESSAGE = (
    'Region [{region}] is not supported. Supported regions are: {supported}.'
)

_PROJECT_MESSAGE = 'Please select the project to use:'
_SINGLE_PROJECT_MESSAGE = 'One project found and selected: {project}.'


def HandleUserInputToS(
    tos_ids: list[str],
    auto_accept_tos_ids: list[str] | None = None,
) -> list[str]:
  """Prompts the user to accept each TOS in the provided list of TOS IDs.

  All terms of service requiring user acceptance are presented together in a
  single prompt, allowing the user to accept or decline once.

  Args:
    tos_ids: List of TOS IDs to prompt the user for.
    auto_accept_tos_ids: Optional list of TOS IDs to automatically accept
      without prompting.

  Returns:
    List of TOS IDs accepted by the user.

  Raises:
    InvalidTosIdError: If any ToS ID in `auto_accept_tos_ids` is not in
      `VALID_TOS_IDS`.
  """
  if auto_accept_tos_ids:
    ValidateTosIds(auto_accept_tos_ids)

  if not tos_ids:
    return []

  auto_accept_set = set(auto_accept_tos_ids) if auto_accept_tos_ids else set()

  to_prompt_ids = set()
  for tos_id in tos_ids:
    if tos_id in auto_accept_set:
      continue
    if tos_id not in _TOS_REGISTRY:
      log.warning(f'Unrecognized ToS ID: [{tos_id}]')
      telemetry.RecordEvent(telemetry.UNRECOGNIZED_TOS_ID_KEY, tos_id)
      continue
    to_prompt_ids.add(tos_id)

  auto_accepted = [tos_id for tos_id in tos_ids if tos_id in auto_accept_set]
  if not to_prompt_ids:
    if auto_accepted:
      telemetry.RecordEvent(telemetry.TOS_DECISION_KEY, telemetry.DECISION_FLAG)
    return auto_accepted

  # Deduplicate ToS to display by (title, url), ordered by canonical order.
  tos_info_list = list(
      dict.fromkeys(
          _TOS_REGISTRY[tos_id]
          for tos_id in VALID_TOS_IDS
          if tos_id in to_prompt_ids
      )
  )

  message = _FormatMessage(tos_info_list)
  prompt_string = _FormatPromptString([info.title for info in tos_info_list])

  can_prompt = console_io.CanPrompt()
  accepted = console_io.PromptContinue(
      message=message,
      prompt_string=prompt_string,
      default=False,
  )

  if not can_prompt:
    # Unattended runs fall back to the prompt default, so the result does not
    # reflect an explicit user decision.
    decision = telemetry.DECISION_UNATTENDED
  elif accepted:
    decision = telemetry.DECISION_CONFIRMED
  else:
    decision = telemetry.DECISION_DECLINED
  telemetry.RecordEvent(telemetry.TOS_DECISION_KEY, decision)

  if not accepted:
    return auto_accepted

  return [
      tos_id
      for tos_id in tos_ids
      if tos_id in auto_accept_set or tos_id in _TOS_REGISTRY
  ]


def HandleUserInputSelectRegion(
    regions: list[str],
    default_region: str,
) -> str:
  """Prompts the user to select a region for provisioning project resources.

  Args:
    regions: List of region strings to choose from.
    default_region: Default region value to fall back to.

  Returns:
    The region selected by the user.
  """
  if not regions:
    return default_region

  default_idx = (
      regions.index(default_region)
      if default_region and default_region in regions
      else None
  )

  idx = console_io.PromptChoice(
      regions,
      default=default_idx,
      message=_REGION_MESSAGE,
  )
  return regions[idx] if idx is not None else default_region


def FormatProject(project: onboarding_messages.Project) -> str:
  """Formats a project for display to the user."""
  if project.displayName:
    return f'{project.displayName} [{project.name}]'
  return f'[{project.name}]'


def HandleUserInputSelectProject(
    projects: Sequence[onboarding_messages.Project],
) -> onboarding_messages.Project | None:
  """Prompts the user to select a project to use for onboarding.

  If exactly one project is available, it is selected automatically without
  prompting, and the user is informed of the selection. Otherwise, the first
  project is the default, chosen if the user presses Enter without a value or
  if prompts are disabled.

  Args:
    projects: Projects the user can select from.

  Returns:
    The project selected by the user (or the only/default project), or None
    if there are no projects to select from or the user chose to cancel.
  """
  if not projects:
    return None

  if len(projects) == 1:
    project = projects[0]
    log.status.Print(
        _SINGLE_PROJECT_MESSAGE.format(project=FormatProject(project))
    )
    telemetry.RecordEvent(
        telemetry.PROJECT_DECISION_KEY, telemetry.DECISION_AUTO_SELECTED
    )
    return project

  can_prompt = console_io.CanPrompt()
  try:
    idx = console_io.PromptChoice(
        [FormatProject(p) for p in projects],
        default=0,
        message=_PROJECT_MESSAGE,
        cancel_option=True,
    )
  except console_io.OperationCancelledError:
    idx = None

  if not can_prompt:
    decision = telemetry.DECISION_UNATTENDED
  elif idx is None:
    decision = telemetry.DECISION_DECLINED
  else:
    decision = telemetry.DECISION_CONFIRMED
  telemetry.RecordEvent(telemetry.PROJECT_DECISION_KEY, decision)
  return projects[idx] if idx is not None else None


def _FormatCloudRegion(region: onboarding_messages.CloudRegion) -> str:
  """Formats a Google Cloud region for display to the user."""
  if region.displayName:
    return f'{region.name} ({region.displayName})'
  return region.name


def HandleUserInputSelectCloudRegion(
    regions: Sequence[onboarding_messages.CloudRegion],
    default_region: onboarding_messages.CloudRegion | None = None,
    selected_region_name: str | None = None,
) -> onboarding_messages.CloudRegion | None:
  """Prompts the user to select a Google Cloud region to use for onboarding.

  This handles Google Cloud regions (e.g. `us-west1`), not geographic region
  codes (e.g. `US`).

  If `selected_region_name` is provided (e.g. from the `--region` flag), the
  matching region is used without prompting. If exactly one region is
  available, it is selected automatically without prompting, and the user is
  informed of the selection. Otherwise, the suggested default region (matched
  by name) is pre-selected, and is chosen if the user presses Enter without a
  value.

  If prompts are disabled (e.g. `--quiet` or a non-interactive session) and a
  choice is required, the available regions are printed and an error is
  raised instead of silently falling back to the default region, so the user
  can rerun the command with `--region`.

  Args:
    regions: Google Cloud regions the user can select from.
    default_region: Optional suggested region to pre-select. Ignored if it is
      not one of `regions`.
    selected_region_name: Optional name of the region to select without
      prompting (e.g. `us-east1`). Matched case-insensitively, ignoring
      surrounding whitespace.

  Returns:
    The region selected by the user (or the only/default region), or None if
    there are no regions to select from, no region was selected, or the user
    chose to cancel.

  Raises:
    calliope_exceptions.InvalidArgumentException: If `selected_region_name`
      is not one of `regions`.
    onboarding_exceptions.CloudRegionNotSelectedError: If prompts are
      disabled and the user must choose between multiple regions.
  """
  if not regions:
    return None

  region_names = [r.name for r in regions]

  if selected_region_name is not None:
    normalized_name = selected_region_name.strip().lower()
    for region in regions:
      if region.name.lower() == normalized_name:
        telemetry.RecordEvent(
            telemetry.CLOUD_REGION_DECISION_KEY,
            telemetry.DECISION_FLAG,
        )
        return region
    telemetry.RecordEvent(
        telemetry.CLOUD_REGION_DECISION_KEY,
        telemetry.DECISION_FLAG_INVALID,
    )
    raise calliope_exceptions.InvalidArgumentException(
        REGION_FLAG,
        _UNSUPPORTED_CLOUD_REGION_MESSAGE.format(
            region=selected_region_name,
            supported=', '.join(region_names),
        ),
    )

  if len(regions) == 1:
    region = regions[0]
    log.status.Print(
        _SINGLE_CLOUD_REGION_MESSAGE.format(region=_FormatCloudRegion(region))
    )
    telemetry.RecordEvent(
        telemetry.CLOUD_REGION_DECISION_KEY,
        telemetry.DECISION_AUTO_SELECTED,
    )
    return region

  if not console_io.CanPrompt():
    # Don't silently fall back to the default region when unattended. Instead,
    # list the options in the error so the user can rerun with an explicit
    # selection. The list is part of the error (rather than status output) so
    # it is shown even if status output is suppressed (e.g.
    # --no-user-output-enabled).
    default_name = default_region.name if default_region else None
    available = '\n'.join(
        f' - {name}'
        + (_SUGGESTED_CLOUD_REGION_SUFFIX if name == default_name else '')
        for name in region_names
    )
    telemetry.RecordEvent(
        telemetry.CLOUD_REGION_DECISION_KEY, telemetry.DECISION_UNATTENDED
    )
    raise onboarding_exceptions.CloudRegionNotSelectedError(
        _CLOUD_REGION_REQUIRED_MESSAGE.format(
            flag=REGION_FLAG,
            available_message=_AVAILABLE_CLOUD_REGIONS_MESSAGE,
            available=available,
        )
    )

  default_idx = (
      region_names.index(default_region.name)
      if default_region and default_region.name in region_names
      else None
  )

  try:
    idx = console_io.PromptChoice(
        [_FormatCloudRegion(r) for r in regions],
        default=default_idx,
        message=_REGION_MESSAGE,
        cancel_option=True,
    )
  except console_io.OperationCancelledError:
    idx = None

  if idx is None:
    decision = telemetry.DECISION_DECLINED
  else:
    decision = telemetry.DECISION_CONFIRMED
  telemetry.RecordEvent(telemetry.CLOUD_REGION_DECISION_KEY, decision)
  return regions[idx] if idx is not None else None
