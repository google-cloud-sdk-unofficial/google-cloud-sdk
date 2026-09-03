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

from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

CLOUD_EXPRESS_TOS_ID = 'cloud-express'

_TOS_MESSAGE = (
    'To use Google Cloud Starter Tier, you must accept the Starter Tier'
    ' Additional Terms of Service.\nRead the terms here:'
    ' https://cloud.google.com/terms/starter-tier-additional-terms-of-service'
)
_TOS_PROMPT = (
    'Do you accept the Google Cloud Starter Tier Additional Terms of Service?'
)

_REGION_MESSAGE = (
    'Please select the region where resources (Cloud Run, Firebase, CloudSQL)'
    ' associated with your project will be provisioned in:\n'
)


def _HandleSingleToS(tos_id: str) -> bool:
  """Handles prompting for a single TOS ID.

  Args:
    tos_id: The ID of the TOS to prompt for.

  Returns:
    True if accepted, False otherwise.
  """
  if tos_id == CLOUD_EXPRESS_TOS_ID:
    return console_io.PromptContinue(
        message=_TOS_MESSAGE,
        prompt_string=_TOS_PROMPT,
        default=False,
    )
  log.warning('Unrecognized ToS ID: [{}]'.format(tos_id))
  return False


def HandleUserInputToS(
    tos_ids: list[str],
    auto_accept_tos_ids: list[str] | None = None,
) -> list[str]:
  """Prompts the user to accept each TOS in the provided list of TOS IDs.

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

  accepted_tos_ids = []
  for tos_id in tos_ids:
    if tos_id in auto_accept_set:
      accepted_tos_ids.append(tos_id)
    elif _HandleSingleToS(tos_id):
      accepted_tos_ids.append(tos_id)
  return accepted_tos_ids


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

  default_idx = None
  if default_region and default_region in regions:
    default_idx = regions.index(default_region)

  idx = console_io.PromptChoice(
      regions,
      default=default_idx,
      message=_REGION_MESSAGE,
  )
  return regions[idx] if idx is not None else default_region
