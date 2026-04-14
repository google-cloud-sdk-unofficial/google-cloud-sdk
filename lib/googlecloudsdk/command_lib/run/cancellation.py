# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Wrapper around serverless_operations CancelFoo for surfaces."""

import dataclasses
from typing import Literal, TypeAlias

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.core.console import progress_tracker

# The cancellation reason that will appear in the resource's terminal condition
_Reason: TypeAlias = Literal['Cancelled', 'Stopped']


@dataclasses.dataclass(frozen=True)
class _ProgressStatusMessages:
  """Progress status messages."""

  header: str
  failed: str
  already_done: str


class CancellationPoller(waiter.OperationPoller):
  """Polls for cancellation of a resource."""

  def __init__(self, getter):
    """Supply getter as the resource getter."""
    self._getter = getter
    self._ret = None

  def IsDone(self, obj):
    return obj is None or obj.conditions.IsTerminal()

  def Poll(self, ref):
    self._ret = self._getter(ref)
    return self._ret

  def GetMessage(self):
    if self._ret and self._ret.conditions:
      return self._ret.conditions.DescriptiveMessage() or ''
    return ''

  def GetResult(self, obj):
    return obj


def Cancel(
    ref, getter, canceller, async_, expected_reason: _Reason = 'Cancelled'
):
  """Cancels a resource for a surface, including a pretty progress tracker."""
  if async_:
    canceller(ref)
    return
  poller = CancellationPoller(getter)
  messages = _ProgressMessages(ref.Name(), expected_reason)
  with progress_tracker.ProgressTracker(
      message=messages.header,
      detail_message_callback=poller.GetMessage,
  ):
    canceller(ref)
    res = waiter.PollUntilDone(poller, ref)
    if not res:
      raise serverless_exceptions.CancellationFailedError(messages.failed)
    if res.conditions.IsReady():
      raise serverless_exceptions.CancellationFailedError(messages.already_done)
    if res.conditions.TerminalConditionReason() != expected_reason:
      if poller.GetMessage():
        raise serverless_exceptions.CancellationFailedError(
            f'{messages.failed[:-1]}: {poller.GetMessage()}'
        )
      else:
        raise serverless_exceptions.CancellationFailedError(messages.failed)


def _ProgressMessages(
    name: str, expected_reason: _Reason
) -> _ProgressStatusMessages:
  """Status messages to be printed by the progress tracker."""
  if expected_reason == 'Stopped':
    return _ProgressStatusMessages(
        header=f'Stopping [{name}]',
        failed=f'Failed to stop [{name}].',
        already_done=(
            f'[{name}] has completed successfully before it could be stopped.'
        ),
    )
  return _ProgressStatusMessages(
      header=f'Cancelling [{name}]',
      failed=f'Failed to cancel [{name}].',
      already_done=(
          f'[{name}] has completed successfully before it could be cancelled.'
      ),
  )
