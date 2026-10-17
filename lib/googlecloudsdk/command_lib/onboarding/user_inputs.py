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

import dataclasses

from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

CLOUD_TOS_ID = 'cloud'
STARTER_TIER_TOS_ID = 'starter-tier-additional-terms-of-service'
PANTHEON_TOS_ID = 'pantheon'
FREE_TRIAL_TOS_ID = 'cloud-free-trial'

_TOS_HEADER = (
    'To provision resources on the starter tier, review and accept the terms of'
    ' service:'
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
}

VALID_TOS_IDS = tuple(_TOS_REGISTRY)


def _FormatMessage(tos_list: list[_ToSInfo]) -> str:
  """Formats the terms of service message."""
  if len(tos_list) == 1:
    items = [f'• {tos_list[0].title} ({tos_list[0].url})']
  else:
    items = [
        f'{i}. {tos.title} ({tos.url})' for i, tos in enumerate(tos_list, 1)
    ]
  return '\n'.join([_TOS_HEADER] + items)


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
  """
  if not tos_ids:
    return []

  auto_accept_set = set(auto_accept_tos_ids) if auto_accept_tos_ids else set()

  to_prompt_ids = set()
  for tos_id in tos_ids:
    if tos_id in auto_accept_set:
      continue
    if tos_id not in _TOS_REGISTRY:
      log.warning(f'Unrecognized ToS ID: [{tos_id}]')
      continue
    to_prompt_ids.add(tos_id)

  auto_accepted = [tos_id for tos_id in tos_ids if tos_id in auto_accept_set]
  if not to_prompt_ids:
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

  accepted = console_io.PromptContinue(
      message=message,
      prompt_string=prompt_string,
      default=False,
  )

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
