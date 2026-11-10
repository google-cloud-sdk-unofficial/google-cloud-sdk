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
"""Manage and stream DAG progress and stage logs for Cloud Build Pipelines."""

import collections
import importlib
import io
import queue
import sys
import threading
import time
import warnings

from apitools.base.py import encoding as apitools_encoding
from apitools.base.py import exceptions as api_exceptions
from google.auth import exceptions as google_auth_exceptions
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import logs as cb_logs
from googlecloudsdk.api_lib.logging import common
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_attr_os
from googlecloudsdk.core.console.style import mappings as style_mappings
from googlecloudsdk.core.console.style import parser as style_parser
from googlecloudsdk.core.util import times
import six

# TODO(b/581140384): Replace plain-string execution state, step status, and
# failure type constants with module-level Python enum.Enums once the
# PipelineRun interactive execution stack lands.
TERMINAL_RUN_STATES = frozenset([
    'SUCCEEDED',
    'FAILED',
    'CANCELLED',
    'TIMED_OUT',
    'SKIPPED',
])

FAILURE_RUN_STATES = frozenset([
    'FAILED',
    'CANCELLED',
    'TIMED_OUT',
])

ACTIVE_STEP_STATUSES = frozenset([
    'WORKING',
    'SUCCESS',
    'FAILURE',
    'INTERNAL_ERROR',
    'TIMEOUT',
    'CANCELLED',
    'EXPIRED',
])

# Server-side ordering window (`TailLogEntriesRequest.buffer_window`,
# `(0, 60s]`, defaults to 2s on the server) passed when opening the
# bidirectional gRPC `TailLogEntries` stream. Setting `buffer_window_seconds=1`
# reduces the Cloud Logging server hold latency from 2s to 1s.
GCL_TAIL_BUFFER_WINDOW_SECONDS = 1

# Maximum number of trailing log entries fetched per failed stage in
# PrintFailedStageLogs (`order_by='DESC'`) so large stage builds do not paginate
# through their entire log history at 1,000 entries per RPC.
FAILED_STAGE_LOG_TAIL_LIMIT = 100

# Single-page cap (`entries.list` max pageSize=1000, `order_by='DESC'` reversed)
# for one-shot catch-up and terminal stage flushes in PollActiveStages.
ONE_SHOT_LOG_TAIL_LIMIT = 1000

# Exponential retry backoff bounds when one-shot `FetchLogs` hits transient
# Cloud Logging quota (HTTP 429) or server (HTTP 5xx) errors during streaming.
FETCH_LOGS_BACKOFF_INITIAL_SEC = 5.0
FETCH_LOGS_BACKOFF_MAX_SEC = 30.0

_BENIGN_TAIL_WARNING_PREFIXES = (
    'The maximum duration for tail has been met.',
    'In total, suppressed ',
    'Find guidance for suppression at ',
)

_STREAM_CLOSE_JOIN_TIMEOUT_SECONDS = 0.2

STREAM_LOGS_UNAVAILABLE_ERROR = (
    'ERROR: --stream-logs requires a gcloud version with gRPC support '
    '(update gcloud, or install grpcio and set '
    'CLOUDSDK_PYTHON_SITEPACKAGES=1). Running without --stream-logs instead.'
)

STREAM_LOGS_SESSION_ERROR = (
    'ERROR: Cloud Logging live stream (--stream-logs) could not be opened; '
    'running without --stream-logs instead.'
)

# Fixed sleep interval between GetPipelineRun status polls.
POLL_INTERVAL_SEC = 1.0

# Granularity at which the poll sleep re-checks for a pending Ctrl+C. The
# SIGINT handler only sets a flag (it must not touch locks, see
# PipelineRunWatcher.RequestCancel), and a plain time.sleep is transparently
# resumed after the handler returns (PEP 475), so the sleep is sliced to keep
# cancellation responsive.
CANCEL_CHECK_INTERVAL_SEC = 0.05

# Redraw cadence of the interactive progress tree, matching
# console.progress_tracker.StagedProgressTracker(tick_delay=0.1). Rendering
# runs on its own daemon thread (as the gcloud progress trackers do) so spinner
# frames and elapsed timers advance on a fixed clock instead of once per
# GetPipelineRun round trip.
TREE_TICK_DELAY_SEC = 0.1


def _TailStreamErrors():
  """Returns concrete exception types a Cloud Logging tail stream may raise."""
  error_types = [
      exceptions.Error,
      google_auth_exceptions.GoogleAuthError,
      api_exceptions.Error,
      OSError,
  ]
  # Resolve gRPC and google.api_core exception bases through sys.modules so
  # importing pipeline_logs never loads optional grpcio when --stream-logs is
  # unused; an instance of either class can only exist once loaded.
  grpc_mod = sys.modules.get('grpc')
  if grpc_mod is not None:
    error_types.append(grpc_mod.RpcError)
  api_core_exc = sys.modules.get('google.api_core.exceptions')
  if api_core_exc is not None:
    error_types.append(api_core_exc.GoogleAPIError)
  return tuple(error_types)


def _CreateLogTailer():
  """Returns a gRPC Cloud Logging `LogTailer`, or None if gRPC is absent."""
  with warnings.catch_warnings():
    # TODO(b/578093012): Remove once the
    # ssl_channel_credentials_with_custom_signer ExperimentalApiWarning in
    # gapic_util_internal.py is resolved.
    warnings.filterwarnings(
        'ignore',
        message=r'.*ssl_channel_credentials_with_custom_signer.*',
        category=Warning,
    )
    try:
      tailing = importlib.import_module(
          'googlecloudsdk.api_lib.logging.tailing'
      )
    except ImportError as e:
      log.debug('gRPC Cloud Logging tailing module unavailable: %s', e)
      return None
    return tailing.LogTailer()


def FormatDuration(start_time_str, end_time_str=None, now_fn=time.time):
  """Formats the duration between start_time_str and end_time_str (or now).

  Args:
    start_time_str: RFC3339 start timestamp string.
    end_time_str: Optional RFC3339 end timestamp string. When None, falls back
      to calling now_fn().
    now_fn: Zero-argument callable returning current epoch seconds when
      end_time_str is None, or None to disable live elapsed fallback.

  Returns:
    Formatted duration string such as '12s', '1m2s', or '1h5m3s', or None if
    start_time_str is empty, any timestamp cannot be parsed, or both
    end_time_str and now_fn are None.
  """
  if not start_time_str:
    return None
  try:
    start_dt = times.ParseDateTime(start_time_str)
    start_ts = times.GetTimeStampFromDateTime(start_dt)
    if end_time_str:
      end_dt = times.ParseDateTime(end_time_str)
      end_ts = times.GetTimeStampFromDateTime(end_dt)
    elif now_fn is not None:
      end_ts = now_fn()
    else:
      return None
  except (times.Error, TypeError, ValueError, OverflowError):
    return None

  total_seconds = max(0, int(round(end_ts - start_ts)))
  if total_seconds < 60:
    return '{}s'.format(total_seconds)
  if total_seconds < 3600:
    return '{}m{}s'.format(total_seconds // 60, total_seconds % 60)
  hours = total_seconds // 3600
  minutes = (total_seconds % 3600) // 60
  seconds = total_seconds % 60
  return '{}h{}m{}s'.format(hours, minutes, seconds)


def ExtractBuildId(build_msg):
  """Extracts the short build ID from an evaluatedBuild message.

  Args:
    build_msg: Cloud Build apitools Build message, or None.

  Returns:
    Short build ID string, or None if build_msg is None or carries neither an
    id nor a resource name with a trailing segment.
  """
  if not build_msg:
    return None
  if build_msg.id:
    return build_msg.id
  if build_msg.name:
    return build_msg.name.rstrip('/').split('/')[-1] or None
  return None


def _StepLabel(step, index):
  """Formats a step label matching Cloud Build worker conventions."""
  raw_label = step.id or step.name or ''
  label = ' '.join(
      part.strip() for part in raw_label.splitlines() if part.strip()
  )
  if label:
    return 'Step #{} - "{}"'.format(index, label)
  return 'Step #{}'.format(index)


def _NormalizeExecState(state_val):
  """Normalizes an ExecutionState enum or string, defaulting to PENDING."""
  if not state_val:
    return 'PENDING'
  # TODO(b/581138859): Replace vestigial six.text_type PY2/PY3 shims with str
  # and remove import six once the PipelineRun execution stack lands.
  state_str = six.text_type(state_val)
  if state_str == 'EXECUTION_STATE_UNSPECIFIED':
    return 'PENDING'
  return state_str


def _NormalizeFailureType(failure_info):
  """Normalizes a StageFailureInfo type enum or string."""
  if not failure_info or not failure_info.type:
    return 'FAILURE'
  raw_type = str(failure_info.type)
  if raw_type == 'FAILURE_TYPE_UNSPECIFIED':
    return 'FAILURE'
  return raw_type


def _HttpStatusCode(err):
  """Extracts an integer HTTP status code from `HttpError`, or None."""
  try:
    return err.status_code
  except (AttributeError, KeyError, TypeError, ValueError):
    return None


def _TimestampEpoch(ts_str):
  """Parses an RFC3339 timestamp string into epoch seconds, or None."""
  if not ts_str:
    return None
  try:
    return times.GetTimeStampFromDateTime(times.ParseDateTime(ts_str))
  except (times.Error, TypeError, ValueError, OverflowError):
    return None


def _EarliestTimestamp(timestamps):
  """Returns the chronologically earliest timestamp string from `timestamps`."""
  best_ts = None
  best_key = None
  for ts in timestamps:
    if not ts:
      continue
    epoch = _TimestampEpoch(ts)
    key = (0, epoch, ts) if epoch is not None else (1, 0.0, ts)
    if best_key is None or key < best_key:
      best_key = key
      best_ts = ts
  return best_ts


class PipelineTreeTracker(object):
  """Renders a collapsible 2-level DAG progress tree on stderr."""

  def __init__(self, out=None, is_tty=None, now_fn=time.time, console=None):
    """Initializes the instance.

    Args:
      out: Output writer (`log.status` ConsoleWriter or `io.IOBase` stream). If
        None, defaults to `log.status`.
      is_tty: Optional boolean overriding interactive ANSI TTY detection. If
        None, auto-detected from `out.isatty()`, ANSI support, and screen
        reader accessibility settings.
      now_fn: Zero-argument callable returning current epoch seconds.
      console: Optional `console_attr.ConsoleAttr` override. If None, uses
        `console_attr.GetConsoleAttr()`.
    """
    self._out = out if out is not None else log.status
    self._respect_user_output = out is None or out is log.status
    self._now_fn = now_fn
    self._console_attr = console or console_attr.GetConsoleAttr()
    screen_reader = properties.VALUES.accessibility.screen_reader.GetBool()
    if is_tty is not None:
      self._is_tty = is_tty
    else:
      try:
        stream_is_tty = bool(self._out.isatty())
      except AttributeError:
        stream_is_tty = False
      supports_ansi = self._console_attr.SupportsAnsi()
      self._is_tty = stream_is_tty and supports_ansi and not screen_reader

    self._prev_line_count = 0
    self._ticks = 0
    self._last_stage_states = {}
    self._last_step_states = {}
    self._symbols = self._console_attr.GetProgressTrackerSymbols()
    mappings = (
        style_mappings.GetStyleMappings(self._console_attr)
        if self._is_tty
        else style_mappings.STYLE_MAPPINGS_BASIC
    )
    self._parser = style_parser.GetTypedTextParser(
        enabled=self._is_tty,
        style_mappings=mappings,
    )
    is_utf8 = self._console_attr.GetEncoding() == 'utf-8' and not screen_reader
    self._dot_sym = '·' if is_utf8 else '-'

  @property
  def is_interactive(self):
    """True when the tree is redrawn in place with ANSI cursor control."""
    return self._is_tty

  def _CurrentSpinMark(self):
    """Returns the current spinner frame from ProgressTrackerSymbols."""
    spin_marks = self._symbols.spin_marks
    if not spin_marks:
      return '*'
    return spin_marks[self._ticks % len(spin_marks)]

  def _FormatPrefix(self, mark):
    """Formats a symbol with gcloud ProgressTrackerSymbols column padding."""
    pad = ' ' * max(1, self._symbols.prefix_length - len(mark))
    return self._parser.ParseTypedTextToString(mark) + pad

  def _RunPrefix(self, state_str):
    """Returns the formatted status prefix for the overall PipelineRun."""
    if state_str == 'SUCCEEDED':
      return self._FormatPrefix(self._symbols.success)
    if state_str == 'SKIPPED':
      return self._FormatPrefix(self._symbols.interrupted)
    if state_str in FAILURE_RUN_STATES:
      return self._FormatPrefix(self._symbols.failed)
    return self._FormatPrefix(self._CurrentSpinMark())

  def _StepPrefix(self, status_str):
    """Returns the formatted status prefix for an individual child BuildStep."""
    if status_str == 'SUCCESS':
      return self._FormatPrefix(self._symbols.success)
    if status_str == 'WORKING':
      return self._FormatPrefix(self._CurrentSpinMark())
    if status_str in (
        'FAILURE',
        'INTERNAL_ERROR',
        'TIMEOUT',
        'CANCELLED',
        'EXPIRED',
    ):
      return self._FormatPrefix(self._symbols.failed)
    return self._FormatPrefix(self._symbols.not_started)

  def RenderLines(self, run, is_terminal=False):
    """Builds the list of lines for the 2-level STAGES -> Steps tree.

    Args:
      run: Cloud Build apitools PipelineRun message to render.
      is_terminal: True when rendering the final completed snapshot of the run.

    Returns:
      List of formatted tree lines without trailing newlines.

    Raises:
      exceptions.Error: If run or any stage is missing required identifiers or
        build status submessages.
    """
    if not run or not run.name or not run.pipeline:
      raise exceptions.Error(
          'PipelineRun is missing required name or pipeline resource path.'
      )
    pipeline_id = run.pipeline.split('/')[-1]
    run_id = run.name.split('/')[-1]
    run_state = _NormalizeExecState(run.state)
    run_prefix = self._RunPrefix(run_state)

    if is_terminal or run_state in TERMINAL_RUN_STATES:
      duration = FormatDuration(run.startTime, run.finishTime, now_fn=None)
      status_part = (
          '({} in {})'.format(run_state, duration)
          if duration
          else '({})'.format(run_state)
      )
    else:
      duration = FormatDuration(run.startTime, None, now_fn=self._now_fn)
      status_part = (
          '({} {} {} elapsed)'.format(run_state, self._dot_sym, duration)
          if duration
          else '({})'.format(run_state)
      )

    lines = [
        '{}{} {} {} {}'.format(
            run_prefix, pipeline_id, self._dot_sym, run_id, status_part
        ),
        '',
        'STAGES',
    ]

    depends_on_by_stage = {}
    if run.configSnapshot:
      for config_stage in run.configSnapshot.stages:
        depends_on_by_stage[config_stage.id] = config_stage.dependsOn

    run_failed = (
        run_state in TERMINAL_RUN_STATES and run_state != 'SUCCEEDED'
    )

    for stage in run.stages:
      if not stage.id or not stage.build:
        raise exceptions.Error(
            'PipelineRun stage is missing required id or build state.'
        )
      stage_id = stage.id
      build_stage = stage.build
      raw_state = _NormalizeExecState(build_stage.state)

      # Normalize unstarted PENDING stages to SKIPPED once the PipelineRun
      # terminates in a non-SUCCEEDED state (b/551904538).
      if run_failed and raw_state in ('PENDING', 'SKIPPED'):
        stage_state = 'SKIPPED'
      else:
        stage_state = raw_state

      eval_build = build_stage.evaluatedBuild
      build_id = ExtractBuildId(eval_build)
      build_suffix = ' (build {})'.format(build_id) if build_id else ''

      stage_dur = FormatDuration(
          build_stage.startTime, build_stage.endTime, now_fn=None
      )
      dur_suffix = ' in {}'.format(stage_dur) if stage_dur else ''

      if stage_state == 'SUCCEEDED':
        lines.append(
            '{}{}{}{}'.format(
                self._FormatPrefix(self._symbols.success),
                stage_id,
                dur_suffix,
                build_suffix,
            )
        )
      elif stage_state == 'RUNNING':
        lines.append(
            '{}{}{}'.format(
                self._FormatPrefix(self._CurrentSpinMark()),
                stage_id,
                build_suffix,
            )
        )
        lines.extend(self._RenderStepLines(eval_build))
      elif stage_state in FAILURE_RUN_STATES:
        lines.append(
            '{}{}{}{}'.format(
                self._FormatPrefix(self._symbols.failed),
                stage_id,
                dur_suffix,
                build_suffix,
            )
        )
        step_lines = self._RenderStepLines(eval_build)
        if step_lines:
          lines.extend(step_lines)
        elif stage.failureInfo and stage.failureInfo.detail:
          raw_fail_type = (
              six.text_type(stage.failureInfo.type)
              if stage.failureInfo.type
              else ''
          )
          fail_type = (
              raw_fail_type
              if raw_fail_type and raw_fail_type != 'FAILURE_TYPE_UNSPECIFIED'
              else 'FAILURE'
          )
          detail = ' '.join(
              part.strip()
              for part in stage.failureInfo.detail.splitlines()
              if part.strip()
          )
          lines.append(
              '  {}{}: {}'.format(
                  self._FormatPrefix(self._symbols.failed),
                  fail_type,
                  detail,
              )
          )
      elif stage_state == 'SKIPPED':
        skipped_prefix = self._FormatPrefix(self._symbols.interrupted)
        deps = depends_on_by_stage.get(stage_id, [])
        if deps:
          lines.append(
              '{}{} (skipped {} depends on: {})'.format(
                  skipped_prefix, stage_id, self._dot_sym, ', '.join(deps)
              )
          )
        else:
          lines.append('{}{} (skipped)'.format(skipped_prefix, stage_id))
      else:
        pending_prefix = self._FormatPrefix(self._symbols.not_started)
        deps = depends_on_by_stage.get(stage_id, [])
        if deps:
          lines.append(
              '{}{} (depends on: {})'.format(
                  pending_prefix, stage_id, ', '.join(deps)
              )
          )
        else:
          lines.append('{}{}'.format(pending_prefix, stage_id))

    return lines

  def _RenderStepLines(self, build_msg):
    """Renders indented step lines for a RUNNING or FAILED stage build."""
    if not build_msg:
      return []
    step_lines = []
    for index, step in enumerate(build_msg.steps):
      status_str = six.text_type(step.status) if step.status else 'QUEUED'
      if status_str not in ACTIVE_STEP_STATUSES:
        continue
      step_prefix = self._StepPrefix(status_str)
      label = _StepLabel(step, index)
      timing = step.timing
      step_duration = None
      if timing and status_str != 'WORKING':
        step_duration = FormatDuration(
            timing.startTime,
            timing.endTime,
            now_fn=None,
        )
      if step_duration:
        step_lines.append(
            '  {}{} ({})'.format(step_prefix, label, step_duration)
        )
      else:
        step_lines.append('  {}{}'.format(step_prefix, label))
    return step_lines

  def Update(self, run, is_terminal=False):
    """Updates the console with the current PipelineRun state.

    Args:
      run: Cloud Build apitools PipelineRun message to display.
      is_terminal: True when emitting the final completed state of the run.
    """
    if (
        properties.VALUES.core.interactive_ux_style.Get()
        == properties.VALUES.core.InteractiveUXStyles.OFF.name
    ):
      return
    if self._respect_user_output and not log.IsUserOutputEnabled():
      return
    lines = self.RenderLines(run, is_terminal=is_terminal)
    if not is_terminal:
      self._ticks += 1
    if self._is_tty:
      self._RenderAnsi(lines)
    else:
      self._RenderNonTty(run, lines, is_terminal=is_terminal)

  def _TruncateLine(self, line, max_width):
    """Truncates `line` to at most `max_width` display columns."""
    chunks = []
    used = 0
    done = False
    for normal, control in self._console_attr.SplitIntoNormalAndControl(line):
      for character in normal:
        char_width = max(0, console_attr.GetCharacterDisplayWidth(character))
        if used + char_width > max_width:
          done = True
          break
        chunks.append(character)
        used += char_width
      if done:
        break
      chunks.append(control)
    return ''.join(chunks)

  def _RenderAnsi(self, lines):
    """Rewrites the multiline tree in-place using ANSI cursor control."""
    width, _ = console_attr_os.GetTermSize()
    max_width = max(1, width - 1) if (width and width > 0) else 120

    output_chunks = []
    if self._prev_line_count > 0:
      output_chunks.append('\x1b[{}A'.format(self._prev_line_count))

    for line in lines:
      if self._console_attr.DisplayWidth(line) > max_width:
        truncated = self._TruncateLine(line, max_width)
        if '\x1b[' in truncated:
          truncated += '\x1b[39;0m'
      else:
        truncated = line
      output_chunks.append('\r\x1b[2K{}\n'.format(truncated))

    if self._prev_line_count > len(lines):
      extra = self._prev_line_count - len(lines)
      for _ in range(extra):
        output_chunks.append('\r\x1b[2K\n')
      output_chunks.append('\x1b[{}A'.format(extra))

    self._prev_line_count = len(lines)
    stream = (
        self._out
        if isinstance(self._out, io.IOBase)
        else self._out.GetConsoleWriterStream()
    )
    if stream is not None:
      stream.write(''.join(output_chunks))
      stream.flush()

  def _PrintLine(self, text):
    """Writes a line to Cloud SDK ConsoleWriter or a standard Python stream."""
    if isinstance(self._out, io.IOBase):
      self._out.write(text + '\n')
      self._out.flush()
    else:
      self._out.Print(text)

  def _RenderNonTty(self, run, lines, is_terminal=False):
    """Emits discrete transition lines on non-TTY streams and final tree."""
    run_state = _NormalizeExecState(run.state)
    run_failed = (
        run_state in TERMINAL_RUN_STATES and run_state != 'SUCCEEDED'
    )
    if not is_terminal or self._last_stage_states:
      for stage in run.stages:
        stage_id = stage.id
        build_stage = stage.build
        raw_state = _NormalizeExecState(build_stage.state)
        state_str = (
            'SKIPPED'
            if (run_failed and raw_state in ('PENDING', 'SKIPPED'))
            else raw_state
        )
        if self._last_stage_states.get(stage_id) != state_str:
          self._last_stage_states[stage_id] = state_str
          if state_str != 'PENDING':
            self._PrintLine('[stage: {}] {}'.format(stage_id, state_str))
        eval_build = build_stage.evaluatedBuild
        if eval_build:
          for idx, step in enumerate(eval_build.steps):
            step_status = (
                six.text_type(step.status) if step.status else 'QUEUED'
            )
            key = (stage_id, idx)
            if (
                step_status in ACTIVE_STEP_STATUSES
                and self._last_step_states.get(key) != step_status
            ):
              self._last_step_states[key] = step_status
              self._PrintLine(
                  '[stage: {}] {} {}'.format(
                      stage_id, _StepLabel(step, idx), step_status
                  )
              )
    if is_terminal:
      self._PrintLine('\n' + '\n'.join(lines) + '\n')


class _LiveLogStream(object):
  """One bidirectional gRPC `TailLogEntries` session for a fixed build set.

  Every wave of `RUNNING` stage builds gets its own instance, so a worker
  thread left over from a superseded wave can only touch its own flags and
  never the state of the wave that replaced it. `self._tailer.close()` is
  serialized with a per-session lock, and the only other objects shared across
  threads are `queue.Queue` and `threading.Event`, which are thread-safe.
  """

  def __init__(self, tailer, entry_queue):
    self._tailer = tailer
    self._queue = entry_queue
    self._thread = None
    self._closed = threading.Event()
    self._close_lock = threading.Lock()
    self.build_ids = ()
    # Set by the worker on a non-benign warning or an exception.
    self.failed = threading.Event()
    # Set once the worker emits its first entry, warns, or exits.
    self.ready = threading.Event()

  @property
  def started(self):
    return self._thread is not None

  def Serves(self, build_ids):
    """Returns whether this session is live and streaming `build_ids`."""
    return (
        self.started
        and not self._closed.is_set()
        and not self.failed.is_set()
        and self.build_ids == tuple(build_ids)
        and self._thread.is_alive()
    )

  def Start(self, parent, log_filter, build_ids):
    """Spawns the daemon worker thread; returns the `ready` event."""
    self.build_ids = tuple(build_ids)
    self._thread = threading.Thread(
        target=self._Run, args=(parent, log_filter), daemon=True
    )
    self._thread.start()
    return self.ready

  def _CloseTailer(self):
    """Closes `self._tailer` under `_close_lock` so teardown never races."""
    with self._close_lock:
      try:
        self._tailer.close()
      except _TailStreamErrors() as e:
        log.debug('Error closing Cloud Logging tailer: %s', e)

  def _OnWarning(self, warning_message):
    """Records a `TailLogs` warning and flags non-benign session errors."""
    warning_text = six.text_type(warning_message)
    log.debug('Cloud Logging tail stream warning: %s', warning_text)
    if not warning_text.startswith(_BENIGN_TAIL_WARNING_PREFIXES):
      if not self._closed.is_set():
        self.failed.set()
    self.ready.set()

  def _Run(self, parent, log_filter):
    """Worker thread body: pumps `TailLogs` entries into the shared queue."""
    try:
      if self._closed.is_set():
        return
      for entry in self._tailer.TailLogs(
          [parent],
          log_filter,
          buffer_window_seconds=GCL_TAIL_BUFFER_WINDOW_SECONDS,
          output_warning=self._OnWarning,
          output_error=log.debug,
          output_debug=log.debug,
      ):
        if self._closed.is_set():
          break
        self._queue.put(entry)
        self.ready.set()
    except _TailStreamErrors() as e:
      log.debug('Cloud Logging tail stream error: %s', e)
      if not self._closed.is_set():
        self.failed.set()
    except ValueError as e:
      # Cython gRPC raises ValueError('Cannot invoke RPC on closed channel!')
      # if Close() tears down the channel while TailLogs is opening the stream.
      if not self._closed.is_set():
        raise
      log.debug('Cloud Logging tail stream closed during startup: %s', e)
    finally:
      self._CloseTailer()
      self.ready.set()

  def Close(self):
    """Cancels the gRPC stream and joins the worker briefly."""
    self._closed.set()
    self._CloseTailer()
    if self._thread is not None and self._thread.is_alive():
      self._thread.join(timeout=_STREAM_CLOSE_JOIN_TIMEOUT_SECONDS)


class _FetchBackoff(object):
  """Retry policy for one-shot `FetchLogs` calls during streaming.

  Transient errors (HTTP 429 / 5xx) back off exponentially; auth or not-found
  errors (401 / 403 / 404) disable one-shot fetches for the rest of the run.
  """

  def __init__(self, now_fn):
    self._now_fn = now_fn
    self.disabled = False
    self._delay_sec = FETCH_LOGS_BACKOFF_INITIAL_SEC
    self._retry_at = 0.0

  def _Now(self):
    return self._now_fn() if self._now_fn is not None else 0.0

  def CanFetch(self, force=False):
    if self.disabled:
      return False
    return force or self._retry_at <= 0.0 or self._Now() >= self._retry_at

  def OnSuccess(self):
    self._delay_sec = FETCH_LOGS_BACKOFF_INITIAL_SEC
    self._retry_at = 0.0

  def OnError(self, err):
    """Records a failed fetch; returns True if the failure is permanent."""
    if _HttpStatusCode(err) in (401, 403, 404):
      self.disabled = True
      return True
    self._retry_at = self._Now() + self._delay_sec
    self._delay_sec = min(self._delay_sec * 2.0, FETCH_LOGS_BACKOFF_MAX_SEC)
    return False


# Per-tick classification of `run.stages` built by
# `StageLogTailer._ClassifyStages`.
_StageSnapshot = collections.namedtuple(
    '_StageSnapshot',
    [
        'max_stage_len',
        'running_build_ids',
        'newly_terminal_build_ids',
        'newly_terminal_stages',
        'pre_dispatch_lines',
        'pre_dispatch_stages',
        'start_time_by_build_id',
    ],
)


class StageLogTailer(cb_logs.TailerBase):
  """Streams Cloud Logging stage output every 1s via gRPC `TailLogEntries`."""

  def __init__(
      self,
      project_id,
      location,
      out=None,
      now_fn=time.time,
      tailer_factory=None,
  ):
    """Initializes the instance.

    Args:
      project_id: GCP project ID string whose Cloud Logging logs are queried.
      location: Cloud Build region string (for example, `'us-central1'`).
      out: Output writer (`log.status` ConsoleWriter or `io.IOBase` stream). If
        None, defaults to `log.status`.
      now_fn: Zero-argument callable returning current epoch seconds.
      tailer_factory: Zero-argument callable returning a Cloud Logging
        `LogTailer` (or None if gRPC is unavailable). If None, defaults to
        `_CreateLogTailer`.
    """
    self.project_id = project_id
    self.location = location
    self.out = out if out is not None else log.status
    self._parent = 'projects/{}'.format(project_id)
    self._tailer_factory = tailer_factory or _CreateLogTailer
    self._logging_messages = core_apis.GetMessagesModule('logging', 'v2')
    self._seen_entries = set()
    self._printed_header = False
    self._flushed_terminal_stages = set()
    self._caught_up_builds = set()
    self._last_timestamp_by_build_id = {}
    self._fetch_backoff = _FetchBackoff(now_fn)
    self._stage_id_by_build_id = collections.OrderedDict()
    # Shared across waves so entries buffered by a superseded session are still
    # drained on the next tick.
    self._stream_queue = queue.Queue()
    self._stream = None
    self._stream_disabled = False

  def Stop(self):
    """Closes any active background gRPC `TailLogEntries` session."""
    if self._stream is not None:
      stream, self._stream = self._stream, None
      stream.Close()

  def _StreamFailed(self):
    return self._stream is not None and self._stream.failed.is_set()

  def _CreateTailerInstance(self):
    """Instantiates `LogTailer`, returning `(tailer, error_message)`."""
    try:
      tailer = self._tailer_factory()
    except ImportError as e:
      log.debug('gRPC Cloud Logging tailing module unavailable: %s', e)
      return None, STREAM_LOGS_UNAVAILABLE_ERROR
    except _TailStreamErrors() as e:
      log.debug('Unable to initialize gRPC LogTailer: %s', e)
      return None, STREAM_LOGS_SESSION_ERROR
    if tailer is None:
      return None, STREAM_LOGS_UNAVAILABLE_ERROR
    return tailer, None

  def _NewStream(self):
    """Creates an unstarted `_LiveLogStream`, or returns an error message."""
    tailer, error_msg = self._CreateTailerInstance()
    if tailer is None:
      return None, error_msg
    return _LiveLogStream(tailer, self._stream_queue), None

  def CheckAvailable(self):
    """Verifies gRPC `LogTailer` support, printing an error once if absent.

    Returns:
      True if gRPC `LogTailer` support is available, or False otherwise.
    """
    if self._stream_disabled:
      return False
    if self._stream is not None:
      return True
    stream, error_msg = self._NewStream()
    if stream is None:
      self._stream_disabled = True
      self._PrintLogLine(error_msg)
      return False
    self._stream = stream
    return True

  def _MarkStreamUnavailable(self, message):
    """Stops streaming, closes any open header, and prints an error."""
    self._stream_disabled = True
    self.Stop()
    if self._printed_header:
      self._PrintLastLine()
      self._printed_header = False
    self._PrintLogLine(message)

  def _BuildLogFilter(self, build_ids, min_timestamp=None):
    """Builds a Cloud Logging filter matching one or more stage build IDs."""
    build_clauses = [
        'resource.labels.build_id="{}"'.format(bid) for bid in build_ids
    ]
    log_filter = (
        'logName="projects/{project_id}/logs/cloudbuild" AND '
        'resource.type="build" AND ({build_or})'
    ).format(
        project_id=self.project_id,
        build_or=' OR '.join(build_clauses),
    )
    if min_timestamp:
      log_filter += ' AND timestamp>="{}"'.format(min_timestamp)
    return log_filter

  def _FetchLogTail(self, build_ids, min_timestamp, limit):
    """Fetches the newest `limit` entries for `build_ids` in ascending order."""
    entries = list(
        common.FetchLogs(
            log_filter=self._BuildLogFilter(build_ids, min_timestamp),
            order_by='DESC',
            limit=limit,
            parent=self._parent,
        )
    )
    entries.reverse()
    return entries

  def _DrainStreamQueue(self):
    """Drains all currently buffered entries from the gRPC stream queue."""
    drained = []
    while True:
      try:
        drained.append(self._stream_queue.get_nowait())
      except queue.Empty:
        break
    return drained

  def _EnsureGrpcStream(self, running_build_ids):
    """Starts or rotates the 1s gRPC `TailLogEntries` stream for active builds.

    Args:
      running_build_ids: Sequence of `build_id` strings currently in `RUNNING`.

    Returns:
      Tuple `(grpc_active, ready_event)`: `grpc_active` is True when gRPC
      tailing is available, or False when gRPC tailing is unavailable or the
      stream failed. `ready_event` is the `threading.Event` set when a newly
      spawned stream worker emits its first item, warns, or exits, or None when
      `running_build_ids` is empty, the current live stream already serves
      `running_build_ids`, or stream setup failed.
    """
    if self._stream_disabled:
      return False, None
    if self._StreamFailed():
      self._MarkStreamUnavailable(STREAM_LOGS_SESSION_ERROR)
      return False, None
    target_ids = tuple(running_build_ids)
    if not target_ids:
      if self._stream is not None and self._stream.started:
        self.Stop()
      return True, None
    if self._stream is not None and self._stream.Serves(target_ids):
      return True, None

    # Reuse the unstarted session created by CheckAvailable(); otherwise close
    # the superseded wave and open a fresh session for the new build set.
    if self._stream is None or self._stream.started:
      self.Stop()
      stream, error_msg = self._NewStream()
      if stream is None:
        self._MarkStreamUnavailable(error_msg)
        return False, None
      self._stream = stream

    ready_event = self._stream.Start(
        self._parent, self._BuildLogFilter(target_ids), target_ids
    )
    return True, ready_event

  def _ExtractEntryFields(self, entry):
    """Extracts `(insert_id, timestamp_str, build_id, text)` from LogEntry."""
    if isinstance(entry, self._logging_messages.LogEntry):
      labels = (
          apitools_encoding.MessageToDict(entry.resource.labels)
          if (entry.resource and entry.resource.labels)
          else {}
      )
      return (
          entry.insertId or None,
          entry.timestamp or None,
          labels.get('build_id'),
          entry.textPayload or None,
      )

    raw_ts = entry.timestamp
    timestamp_str = None
    if raw_ts is not None and raw_ts.year > 1970:
      try:
        timestamp_str = raw_ts.rfc3339()
      except AttributeError:
        timestamp_str = raw_ts.isoformat()
    build_id = (
        entry.resource.labels.get('build_id')
        if (entry.resource and entry.resource.labels)
        else None
    )
    return (
        entry.insert_id or None,
        timestamp_str,
        build_id,
        entry.text_payload or None,
    )

  def _UpdateBuildWatermark(self, build_id, timestamp_str):
    """Advances the high-water log timestamp recorded for `build_id`."""
    if not build_id or not timestamp_str:
      return
    prev_ts = self._last_timestamp_by_build_id.get(build_id)
    if not prev_ts:
      self._last_timestamp_by_build_id[build_id] = timestamp_str
      return
    new_epoch = _TimestampEpoch(timestamp_str)
    prev_epoch = _TimestampEpoch(prev_ts)
    if new_epoch is not None and prev_epoch is not None:
      if new_epoch >= prev_epoch:
        self._last_timestamp_by_build_id[build_id] = timestamp_str
    elif timestamp_str >= prev_ts:
      self._last_timestamp_by_build_id[build_id] = timestamp_str

  def _EmitStageLine(self, stage_id, max_stage_len, line):
    """Prints a `[<stage-id>]`-aligned line, opening header once if needed."""
    if not self._printed_header:
      self._PrintFirstLine()
      self._printed_header = True
    prefix = '[{}]'.format(stage_id).ljust(max_stage_len + 2)
    self._PrintLogLine('{} {}'.format(prefix, line))

  def _EmitEntries(
      self,
      entries,
      max_stage_len,
      extra_stage_lines=None,
  ):
    """Deduplicates log entries and prints right-padded `[<stage-id>]` lines."""
    if extra_stage_lines:
      for stage_id, lines in extra_stage_lines.items():
        for line in lines:
          self._EmitStageLine(stage_id, max_stage_len, line)

    for entry in entries or ():
      insert_id, timestamp_str, entry_build_id, text = (
          self._ExtractEntryFields(entry)
      )
      resolved_build_id = entry_build_id
      stage_id = self._stage_id_by_build_id.get(entry_build_id)
      if (
          not stage_id
          and not entry_build_id
          and len(self._stage_id_by_build_id) == 1
      ):
        resolved_build_id, stage_id = next(
            iter(self._stage_id_by_build_id.items())
        )
      if not stage_id:
        continue

      self._UpdateBuildWatermark(resolved_build_id, timestamp_str)
      if insert_id:
        dedup_key = (stage_id, insert_id)
        if dedup_key in self._seen_entries:
          continue
        self._seen_entries.add(dedup_key)

      if text:
        clean = self._ValidateScreenReader(text)
        for line in clean.splitlines():
          self._EmitStageLine(stage_id, max_stage_len, line)

  def _FormatStageFailureLines(self, stage):
    """Formats `stage.failureInfo` lines without `[<stage-id>]` prefix."""
    if stage.failureInfo:
      fail_type = _NormalizeFailureType(stage.failureInfo)
      detail = (
          stage.failureInfo.detail or 'Stage failed before build dispatch.'
      )
      clean = self._ValidateScreenReader(detail)
      formatted = []
      for idx, line in enumerate(clean.splitlines()):
        prefix = '{}: '.format(fail_type) if idx == 0 else ''
        formatted.append('{}{}'.format(prefix, line))
      return formatted or ['{}: Stage failed before build dispatch.'.format(
          fail_type
      )]
    return ['Stage failed before build dispatch.']

  def PrintFailedStageLogs(self, run):
    """Fetches and prints Cloud Logging tails for failed or timed-out stages."""
    for stage in run.stages:
      if not stage.id or not stage.build:
        raise exceptions.Error(
            'PipelineRun stage is missing required id or build state.'
        )
      stage_id = stage.id
      build_stage = stage.build
      stage_state = _NormalizeExecState(build_stage.state)
      has_failure_info = bool(stage.failureInfo and stage.failureInfo.detail)
      if stage_state not in ('FAILED', 'TIMED_OUT') and not has_failure_info:
        continue

      header = ' FAILED STAGE OUTPUT [{}] '.format(stage_id)
      self._PrintFirstLine(header)

      eval_build = build_stage.evaluatedBuild
      build_id = ExtractBuildId(eval_build)

      # Pre-dispatch failure (e.g., CEL CONFIG_ERROR) has no child build.
      if not build_id:
        for line in self._FormatStageFailureLines(stage):
          self._PrintLogLine('[{}] {}'.format(stage_id, line))
        self._PrintLastLine()
        continue

      entries = []
      fetch_failed = False
      try:
        entries = self._FetchLogTail(
            [build_id], build_stage.startTime, FAILED_STAGE_LOG_TAIL_LIMIT
        )
      except api_exceptions.HttpError as e:
        # Fall through rather than skipping the stage: `failureInfo` is still
        # available in memory, and `gcloud builds log` can often read the GCS
        # build log even when Cloud Logging denies access.
        fetch_failed = True
        self._PrintLogLine(
            '[{}] Warning: Unable to read Cloud Logging entries ({}).'.format(
                stage_id, e
            )
        )

      printed_any = False
      for entry in entries:
        if entry.textPayload:
          clean = self._ValidateScreenReader(entry.textPayload)
          for line in clean.splitlines():
            self._PrintLogLine('[{}] {}'.format(stage_id, line))
            printed_any = True

      if not printed_any:
        if stage.failureInfo and stage.failureInfo.detail:
          clean_detail = self._ValidateScreenReader(stage.failureInfo.detail)
          for line in clean_detail.splitlines():
            self._PrintLogLine('[{}] {}'.format(stage_id, line))
        elif not fetch_failed:
          # Avoid an empty output block when the tail has no text entries
          # (e.g. LOGGING_GCS_ONLY builds or Cloud Logging ingestion lag).
          self._PrintLogLine(
              '[{}] No Cloud Logging entries found for build {}.'.format(
                  stage_id, build_id
              )
          )

      self._PrintLastLine()
      self._PrintLogLine(
          'To view full logs for this stage, run: gcloud builds log {} '
          '--region={}\n'.format(build_id, self.location)
      )

  def _ClassifyStages(self, stages):
    """Buckets `run.stages` into running, newly terminal, and pre-dispatch."""
    snap = _StageSnapshot(
        max_stage_len=max(len(s.id) for s in stages),
        running_build_ids=[],
        newly_terminal_build_ids=[],
        newly_terminal_stages=[],
        pre_dispatch_lines={},
        pre_dispatch_stages=[],
        start_time_by_build_id={},
    )
    for stage in stages:
      stage_id = stage.id
      build_stage = stage.build
      state_str = _NormalizeExecState(build_stage.state)
      build_id = ExtractBuildId(build_stage.evaluatedBuild)
      if not build_id:
        has_failure_info = bool(stage.failureInfo and stage.failureInfo.detail)
        if (
            (state_str in FAILURE_RUN_STATES or has_failure_info)
            and stage_id not in self._flushed_terminal_stages
        ):
          if stage.failureInfo or state_str != 'CANCELLED':
            snap.pre_dispatch_lines[stage_id] = (
                self._FormatStageFailureLines(stage)
            )
          snap.pre_dispatch_stages.append(stage_id)
        continue
      self._stage_id_by_build_id[build_id] = stage_id
      if build_stage.startTime:
        snap.start_time_by_build_id[build_id] = build_stage.startTime

      if state_str == 'RUNNING':
        snap.running_build_ids.append(build_id)
      elif (
          state_str in TERMINAL_RUN_STATES
          and stage_id not in self._flushed_terminal_stages
      ):
        snap.newly_terminal_build_ids.append(build_id)
        snap.newly_terminal_stages.append(stage_id)
    return snap

  def PollActiveStages(self, run, is_last=False):
    """Streams active stage logs every 1s via gRPC `TailLogEntries`.

    Args:
      run: Current `PipelineRun` message.
      is_last: True on the final terminal flush after run completion.

    Returns:
      bool, True if `--stream-logs` remains active, or False if gRPC tailing is
      unavailable or failed so the caller should run without streaming.
    """
    if self._StreamFailed():
      self._MarkStreamUnavailable(STREAM_LOGS_SESSION_ERROR)
      return False

    stages = run.stages
    if not stages:
      if is_last:
        self.Stop()
        if self._printed_header:
          self._PrintLastLine()
      return True

    for stage in stages:
      if not stage.id or not stage.build:
        raise exceptions.Error(
            'PipelineRun stage is missing required id or build state.'
        )
    snap = self._ClassifyStages(stages)

    if (
        not snap.running_build_ids
        and not snap.newly_terminal_build_ids
        and not snap.pre_dispatch_stages
    ):
      if is_last:
        self.Stop()
      self._EmitEntries(self._DrainStreamQueue(), snap.max_stage_len)
      if is_last and self._printed_header:
        self._PrintLastLine()
      return True

    ready_event = None
    if is_last:
      self.Stop()
    else:
      grpc_active, ready_event = self._EnsureGrpcStream(
          snap.running_build_ids
      )
      if not grpc_active:
        return False

    if ready_event is not None:
      ready_event.wait(timeout=0.02)

    if self._StreamFailed():
      self._MarkStreamUnavailable(STREAM_LOGS_SESSION_ERROR)
      return False

    if ready_event is not None:
      catchup_ids = list(snap.running_build_ids)
    else:
      catchup_ids = [
          bid
          for bid in snap.running_build_ids
          if bid not in self._caught_up_builds
      ]
    flush_ids = list(snap.newly_terminal_build_ids)
    if is_last:
      flush_ids.extend(snap.running_build_ids)
    one_shot_ids = list(
        collections.OrderedDict.fromkeys(catchup_ids + flush_ids)
    )
    floor_timestamps = [
        self._last_timestamp_by_build_id.get(bid)
        or snap.start_time_by_build_id.get(bid)
        for bid in one_shot_ids
    ]
    if one_shot_ids and all(floor_timestamps):
      min_start = _EarliestTimestamp(floor_timestamps)
    else:
      min_start = run.startTime or run.createTime

    # `mark_catchup` / `mark_flushed` record that the one-shot fetch for these
    # builds is settled; a transient error leaves them unmarked so the next
    # tick retries (except terminal stages on the final tick).
    fetched_entries = []
    if not one_shot_ids or self._fetch_backoff.disabled:
      mark_catchup = mark_flushed = True
    elif self._fetch_backoff.CanFetch(force=is_last):
      try:
        fetched_entries = self._FetchLogTail(
            one_shot_ids, min_start, ONE_SHOT_LOG_TAIL_LIMIT
        )
        self._fetch_backoff.OnSuccess()
        mark_catchup = mark_flushed = True
      except api_exceptions.HttpError as e:
        log.warning('Unable to fetch stage logs from Cloud Logging: %s', e)
        permanent = self._fetch_backoff.OnError(e)
        mark_catchup = permanent
        mark_flushed = permanent or is_last
    else:
      mark_catchup = mark_flushed = False
    if mark_catchup:
      self._caught_up_builds.update(catchup_ids)
    if mark_flushed:
      self._flushed_terminal_stages.update(snap.newly_terminal_stages)

    self._flushed_terminal_stages.update(snap.pre_dispatch_stages)
    streamed_entries = self._DrainStreamQueue()
    self._EmitEntries(
        fetched_entries + streamed_entries,
        snap.max_stage_len,
        extra_stage_lines=snap.pre_dispatch_lines,
    )
    if is_last and self._printed_header:
      self._PrintLastLine()
    return True


class PipelineRunWatcher(object):
  """Polls GetPipelineRun until run completion or cancellation.

  Polling and rendering are decoupled, following the gcloud progress tracker
  convention: the calling thread polls `GetPipelineRun` on a fixed sleep
  interval and publishes the latest `PipelineRun` snapshot (including per-step
  progress on `stage.build.evaluatedBuild`), while a daemon ticker thread
  redraws the interactive progress tree every `tick_delay` seconds from the
  latest snapshot. Non-interactive output (CI logs, `--stream-logs`) renders
  inline from the polling thread, since it only prints state transitions.

  Cancellation is two-phase. The SIGINT handler (see `RequestCancel`) only
  records the request; `Watch` observes it on its normal path, on the main
  thread with no locks held, and performs the teardown and the server-side
  cancel from there.
  """

  def __init__(
      self,
      client=None,
      messages=None,
      pipeline_run_ref=None,
      stream_logs=False,
      out=None,
      is_tty=None,
      sleep_fn=None,
      now_fn=time.time,
      tailer_factory=None,
      tick_delay=TREE_TICK_DELAY_SEC,
  ):
    self.client = client or cloudbuild_util.GetClientInstance()
    self.messages = messages or cloudbuild_util.GetMessagesModule()
    self.pipeline_run_ref = pipeline_run_ref
    self.stream_logs = stream_logs
    self.out = out if out is not None else log.status
    self._now_fn = now_fn
    self._sleep_fn = sleep_fn or self._InterruptibleSleep
    self.latest_run = None

    # Written by the SIGINT handler and read by Watch(). Both run on the main
    # thread (Python delivers signal handlers between bytecodes of the main
    # thread), so a plain attribute is sufficient and, unlike a Lock or Event,
    # cannot self-deadlock if the handler fires while Watch() holds a lock.
    self._cancel_requested = False
    self._cancelled = False

    self._tick_delay = tick_delay
    self._render_lock = threading.Lock()
    self._snapshot = None
    self._ticker = None
    self._ticker_stop = threading.Event()

    self._tree_tracker = PipelineTreeTracker(
        out=self.out, is_tty=is_tty, now_fn=self._now_fn
    )
    self._tailer = StageLogTailer(
        project_id=pipeline_run_ref.projectsId,
        location=pipeline_run_ref.locationsId,
        out=self.out,
        now_fn=self._now_fn,
        tailer_factory=tailer_factory,
    )

  @property
  def cancelled(self):
    """True once Watch() stopped early because cancellation was requested."""
    return self._cancelled

  @property
  def cancel_requested(self):
    """True once RequestCancel() was called (before Watch() acts on it)."""
    return self._cancel_requested

  def RequestCancel(self):
    """Records a Ctrl+C request. Safe to call from a signal handler.

    This method deliberately does nothing but set a flag: no locks, no RPCs, no
    output. Signal handlers run on the main thread in the middle of whatever
    Watch() was doing, possibly while it holds `_render_lock`; acquiring it here
    would block forever on a lock owned by the interrupted frame below. Watch()
    performs the actual teardown.
    """
    self._cancel_requested = True

  def _InterruptibleSleep(self, seconds):
    """Sleeps for `seconds`, returning early once cancellation is requested."""
    deadline = time.monotonic() + seconds
    while not self._cancel_requested:
      remaining = deadline - time.monotonic()
      if remaining <= 0:
        return
      time.sleep(min(remaining, CANCEL_CHECK_INTERVAL_SEC))

  def _UsesTicker(self):
    """True when the progress tree should be redrawn by the ticker thread."""
    return bool(self._tick_delay) and self._tree_tracker.is_interactive

  def _StartTicker(self):
    """Starts the daemon thread that redraws the progress tree on a clock."""
    if self._ticker is not None or not self._UsesTicker():
      return
    self._ticker_stop.clear()

    def _Tick():
      # Event.wait returns True once the stop event is set, ending the loop.
      while not self._ticker_stop.wait(self._tick_delay):
        with self._render_lock:
          run = self._snapshot
        if run is None:
          continue
        self._tree_tracker.Update(run, is_terminal=False)

    self._ticker = threading.Thread(
        target=_Tick, name='pipeline-run-tree-ticker'
    )
    self._ticker.daemon = True
    self._ticker.start()

  def _StopTicker(self):
    """Stops and joins the ticker thread so no redraw races the final frame."""
    self._ticker_stop.set()
    if self._ticker is not None:
      self._ticker.join()
      self._ticker = None

  def _ShowProgress(self, run):
    """Publishes the latest state to the ticker, or renders inline."""
    if self._ticker is not None:
      with self._render_lock:
        self._snapshot = run
    else:
      self._tree_tracker.Update(run, is_terminal=False)

  def GetPipelineRun(self):
    """Fetches the current PipelineRun resource from CLH."""
    return self.client.projects_locations_pipelineRuns.Get(
        self.messages.CloudbuildProjectsLocationsPipelineRunsGetRequest(
            name=self.pipeline_run_ref.RelativeName()
        )
    )

  def _CancelPipelineRun(self, run):
    """Requests server-side cancellation after Ctrl+C and reports the outcome.

    Called from Watch() on the main thread after the ticker has been joined and
    the tailer stopped, so the status lines below cannot interleave with a
    progress-tree redraw. If `run` is already terminal there is nothing to
    cancel and only a short notice is printed.

    Args:
      run: The latest `PipelineRun` snapshot observed by Watch().
    """
    run_name = six.text_type(self.pipeline_run_ref)
    if _NormalizeExecState(run.state) in TERMINAL_RUN_STATES:
      log.status.Print(
          'Stopped watching [{r}]; the run already finished with state '
          '{state}.'.format(r=run_name, state=_NormalizeExecState(run.state))
      )
      return

    log.status.Print('Cancelling...')
    try:
      self.client.projects_locations_pipelineRuns.Cancel(
          self.messages.CloudbuildProjectsLocationsPipelineRunsCancelRequest(
              name=self.pipeline_run_ref.RelativeName(),
              cancelPipelineRunRequest=self.messages.CancelPipelineRunRequest(),
          )
      )
    except Exception as e:  # pylint: disable=broad-except
      log.warning(
          'Failed to request cancellation of PipelineRun [%s]: %s',
          self.pipeline_run_ref,
          e,
      )
      log.status.Print(
          'Stopped watching [{r}]; the run is still executing.'.format(
              r=run_name
          )
      )
      return

    # Cancellation is asynchronous on the server: the run is marked CANCELLED
    # and in-flight stage builds are cancelled by the execution manager, so
    # the final stage states are only visible via describe or the Console.
    log.status.Print(
        'Cancel requested for [{r}]. In-flight stage builds are cancelled '
        'asynchronously; check the final state with '
        '`gcloud alpha builds pipeline-runs describe {run_id} '
        '--region={region}`.'.format(
            r=run_name,
            run_id=self.pipeline_run_ref.Name(),
            region=self.pipeline_run_ref.locationsId,
        )
    )

  def Watch(self, initial_run=None):
    """Watches the PipelineRun until it reaches a terminal state or Ctrl+C."""
    run = initial_run or self.GetPipelineRun()
    self.latest_run = run

    try:
      if self.stream_logs and not self._tailer.CheckAvailable():
        self.stream_logs = False
      if not self.stream_logs:
        self._StartTicker()

      while not self._cancel_requested:
        run_state = _NormalizeExecState(run.state)
        if run_state in TERMINAL_RUN_STATES:
          break

        if self.stream_logs:
          if not self._tailer.PollActiveStages(run, is_last=False):
            self.stream_logs = False
            self._StartTicker()
            self._ShowProgress(run)
        else:
          self._ShowProgress(run)

        self._sleep_fn(POLL_INTERVAL_SEC)
        if self._cancel_requested:
          break

        run = self.GetPipelineRun()
        self.latest_run = run

      # Join the ticker before the final frame or the cancel notice so the two
      # never interleave. No locks are held at this point.
      self._StopTicker()
      if self._cancel_requested:
        self._cancelled = True
        self._tailer.Stop()
        self._CancelPipelineRun(run)
      else:
        if self.stream_logs:
          if not self._tailer.PollActiveStages(run, is_last=True):
            self.stream_logs = False
        if not self.stream_logs:
          self._tree_tracker.Update(run, is_terminal=True)
          run_state = _NormalizeExecState(run.state)
          if run_state != 'SUCCEEDED':
            self._tailer.PrintFailedStageLogs(run)
    finally:
      self._StopTicker()
      self._tailer.Stop()

    return run
