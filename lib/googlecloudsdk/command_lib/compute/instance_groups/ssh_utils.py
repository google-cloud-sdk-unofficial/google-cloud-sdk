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

"""SSH utilities for Compute Engine Instance Groups."""

import contextlib
import copy
import os
import sys
import threading

from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files
from surface.compute import ssh as compute_ssh


_THREAD_LOCAL_OUTPUT = threading.local()
_PRINT_LOCK = threading.Lock()


def _PrintPrefixedLines(text: str, instance_name: str, stream_print):
  """Prints each line of text prefixed with [instance_name]."""
  if not text:
    return
  with _PRINT_LOCK:
    for line in text.splitlines():
      stream_print(f'[{instance_name}] {line}')


@contextlib.contextmanager
def _RedirectSshOutputForThreads():
  """Redirects SSHCommand.Run output and propagates extra_flags per thread."""
  original_run = ssh.SSHCommand.Run
  original_parse_flags = ssh.ParseAndSubstituteSSHFlags
  original_exec = execution_utils.Exec

  def _WrappedParseFlags(*parse_args, **parse_kwargs):
    extra_flags = original_parse_flags(*parse_args, **parse_kwargs)
    _THREAD_LOCAL_OUTPUT.extra_flags = extra_flags
    return extra_flags

  def _WrappedRun(self, *run_args, **run_kwargs):
    if not self.extra_flags and getattr(
        _THREAD_LOCAL_OUTPUT, 'extra_flags', None
    ):
      self.extra_flags = list(_THREAD_LOCAL_OUTPUT.extra_flags)
    writer = getattr(_THREAD_LOCAL_OUTPUT, 'writer', None)
    if writer is not None:
      run_kwargs.setdefault('explicit_output_file', writer)
      run_kwargs.setdefault('explicit_error_file', writer)
    return original_run(self, *run_args, **run_kwargs)

  def _WrappedExec(args, *exec_args, **exec_kwargs):
    instance_name = getattr(_THREAD_LOCAL_OUTPUT, 'instance_name', None)
    writer = getattr(_THREAD_LOCAL_OUTPUT, 'writer', None)
    if instance_name and writer is None:
      if 'stdout' not in exec_kwargs and exec_kwargs.get('out_func') is None:
        exec_kwargs['out_func'] = lambda out: _PrintPrefixedLines(
            out, instance_name, log.out.Print
        )
      if 'stderr' not in exec_kwargs and exec_kwargs.get('err_func') is None:
        exec_kwargs['err_func'] = lambda err: _PrintPrefixedLines(
            err, instance_name, log.err.Print
        )
    return original_exec(args, *exec_args, **exec_kwargs)

  ssh.ParseAndSubstituteSSHFlags = _WrappedParseFlags
  ssh.SSHCommand.Run = _WrappedRun
  execution_utils.Exec = _WrappedExec
  try:
    yield
  finally:
    ssh.ParseAndSubstituteSSHFlags = original_parse_flags
    ssh.SSHCommand.Run = original_run
    execution_utils.Exec = original_exec


def ParseBatchSize(batch_size_flag: str, num_instances: int) -> int:
  """Parses the --batch-size flag and validates the flag value.

  Args:
    batch_size_flag: str, batch-size flag argument.
    num_instances: int, total number of target instances.

  Returns:
    int, batch size value capped at num_instances.

  Raises:
    InvalidArgumentException: If batch_size_flag is neither a positive integer
      nor equal to the 'all' keyword.
  """
  if str(batch_size_flag).upper() == 'ALL':
    if num_instances > 100:
      log.warning(
          'Executing ssh command on too many instances simultaneously is '
          'prone to error. Command may fail. Please consider using '
          '`--batch-size` flag if the command fails, for example, '
          '--batch-size=100.'
      )
    return num_instances

  try:
    batch_size = int(batch_size_flag)
    if batch_size > 0:
      return min(batch_size, num_instances)
    raise ValueError()
  except ValueError as error:
    raise exceptions.InvalidArgumentException(
        '--batch-size',
        f'Unable to parse the batch size value {batch_size_flag}. Please use '
        'a positive integer or the keyword "all".',
    ) from error


def _WaitForBatchCompletion(ssh_threads):
  """Waits for all running SSH threads in the current batch to complete.

  Args:
    ssh_threads: List of SSH threads.
  """
  for ssh_thread in ssh_threads:
    ssh_thread.join()


def _FormatSummaryLines(succeeded, failed, skipped=None, indent=''):
  """Formats summary lines for succeeded, failed, and skipped instances."""
  lines = []
  if succeeded:
    lines.append(
        f'{indent}Successfully ran on {len(succeeded)} instance(s): '
        f'{", ".join(succeeded)}'
    )
  else:
    lines.append(f'{indent}Successfully ran on 0 instances.')
  if failed:
    failed_details = ', '.join(
        f'{name} (exit code {code})' for name, code in failed
    )
    lines.append(
        f'{indent}Failed on {len(failed)} instance(s): {failed_details}'
    )
  if skipped:
    lines.append(
        f'{indent}Skipped {len(skipped)} instance(s): {", ".join(skipped)}'
    )
  return lines


def _PrintExecutionSummary(instance_refs, exit_statuses, batch_size=None):
  """Prints an informational summary of succeeded, failed, and skipped instances."""
  if not batch_size or batch_size <= 0:
    batch_size = len(instance_refs) or 1

  batches = [
      list(
          zip(
              instance_refs[i : i + batch_size],
              exit_statuses[i : i + batch_size],
          )
      )
      for i in range(0, len(instance_refs), batch_size)
  ]

  succeeded = []
  failed = []
  skipped = []
  for instance_ref, status in zip(instance_refs, exit_statuses):
    if status == 0:
      succeeded.append(instance_ref.Name())
    elif status is not None:
      failed.append((instance_ref.Name(), status))
    else:
      skipped.append(instance_ref.Name())

  log.status.Print('\n--- Execution Summary ---')
  if len(batches) > 1:
    total_batches = len(batches)
    for batch_idx, batch in enumerate(batches, start=1):
      batch_ran = any(status is not None for _, status in batch)
      if not batch_ran:
        batch_skipped = [ref.Name() for ref, _ in batch]
        log.status.Print(f'Batch {batch_idx}/{total_batches} (not run):')
        log.status.Print(
            f'  Skipped {len(batch_skipped)} instance(s): '
            f'{", ".join(batch_skipped)}'
        )
        continue
      batch_succeeded = [
          ref.Name() for ref, status in batch if status == 0
      ]
      batch_failed = [
          (ref.Name(), status)
          for ref, status in batch
          if status not in (0, None)
      ]
      log.status.Print(f'Batch {batch_idx}/{total_batches}:')
      for line in _FormatSummaryLines(
          batch_succeeded, batch_failed, indent='  '
      ):
        log.status.Print(line)
    log.status.Print('Total:')
    for line in _FormatSummaryLines(succeeded, failed, skipped, indent='  '):
      log.status.Print(line)
  else:
    for line in _FormatSummaryLines(succeeded, failed, skipped):
      log.status.Print(line)


def ListInstanceRefs(holder, ig_ref):
  """Lists RUNNING Compute Engine instance references in the instance group.

  Args:
    holder: ComputeApiHolder instance.
    ig_ref: Parsed compute.instanceGroups or compute.regionInstanceGroups
      resource reference.

  Returns:
    List of parsed compute.instances resource references.
  """
  client = holder.client
  messages = client.messages
  if ig_ref.Collection() == 'compute.regionInstanceGroups' or hasattr(
      ig_ref, 'region'
  ):
    service = client.apitools_client.regionInstanceGroups
    request = messages.ComputeRegionInstanceGroupsListInstancesRequest(
        project=ig_ref.project,
        region=ig_ref.region,
        instanceGroup=ig_ref.Name(),
        regionInstanceGroupsListInstancesRequest=(
            messages.RegionInstanceGroupsListInstancesRequest()
        ),
    )
  else:
    service = client.apitools_client.instanceGroups
    request = messages.ComputeInstanceGroupsListInstancesRequest(
        project=ig_ref.project,
        zone=ig_ref.zone,
        instanceGroup=ig_ref.Name(),
        instanceGroupsListInstancesRequest=(
            messages.InstanceGroupsListInstancesRequest()
        ),
    )

  errors = []
  instances = list(
      request_helper.MakeRequests(
          requests=[(service, 'ListInstances', request)],
          http=client.apitools_client.http,
          batch_url=client.batch_url,
          errors=errors,
      )
  )
  if errors:
    utils.RaiseToolException(errors)

  running_status = (
      messages.InstanceWithNamedPorts.StatusValueValuesEnum.RUNNING
  )
  instance_refs = []
  for item in instances:
    if not item.instance or item.status != running_status:
      continue
    instance_ref = holder.resources.Parse(
        item.instance,
        params={'project': ig_ref.project},
        collection='compute.instances',
    )
    instance_refs.append(instance_ref)
  return instance_refs


def _RunComputeSshForInstance(
    compute_ssh_cmd,
    instance_args,
    instance_name: str,
    idx: int,
    exit_statuses,
    output_directory_path=None,
):
  """Runs gcloud compute ssh logic for a single instance."""
  output_writer = None
  _THREAD_LOCAL_OUTPUT.instance_name = instance_name
  try:
    if output_directory_path:
      log_path = os.path.join(output_directory_path, f'{instance_name}.log')
      output_writer = files.FileWriter(log_path)
      _THREAD_LOCAL_OUTPUT.writer = output_writer
    compute_ssh_cmd.Run(instance_args)
    exit_statuses[idx] = 0
  except SystemExit as e:
    exit_statuses[idx] = e.code if e.code is not None else 0
  except Exception as e:  # pylint: disable=broad-except
    log.status.Print(
        f'SSH command failed on instance [{instance_args.user_host}]: {e}'
    )
    exit_statuses[idx] = 255
  finally:
    _THREAD_LOCAL_OUTPUT.instance_name = None
    if output_writer is not None:
      _THREAD_LOCAL_OUTPUT.writer = None
      output_writer.close()


def RunSshOnInstances(command_instance, args, instance_refs):
  """Executes gcloud compute ssh across all target instances in the group.

  Args:
    command_instance: The Calliope Command instance (self).
    args: Parsed command-line arguments.
    instance_refs: List of compute.instances resource references.
  """
  user = getattr(args, 'user', None)
  # pylint: disable=protected-access
  compute_ssh.Ssh._release_track = base.ReleaseTrack.GA
  compute_ssh_cmd = compute_ssh.Ssh(
      command_instance._cli_do_not_use_directly,
      command_instance.context,
  )
  compute_ssh_cmd._release_track = base.ReleaseTrack.GA
  # pylint: enable=protected-access
  batch_size = ParseBatchSize(args.batch_size, len(instance_refs))
  exit_statuses = [None] * len(instance_refs)
  ssh_threads = []
  current_batch_size = 0

  output_directory_path = None
  if getattr(args, 'output_directory', None):
    output_directory_path = os.path.abspath(
        files.ExpandHomeDir(args.output_directory)
    )

  with _RedirectSshOutputForThreads():
    for idx, instance_ref in enumerate(instance_refs):
      instance_args = copy.copy(args)
      instance_args.user_host = (
          f'{user}@{instance_ref.Name()}' if user else instance_ref.Name()
      )
      instance_args.zone = instance_ref.zone
      instance_args.region = None
      instance_args.container = getattr(args, 'container', None)
      instance_args.troubleshoot = False
      instance_args.ssh_args = None
      if getattr(args, 'ssh_flag', None):
        instance_args.ssh_flag = [
            flag.replace('%NAME%', instance_ref.Name())
            .replace('%ZONE%', instance_ref.zone)
            .replace('%PROJECT%', instance_ref.project)
            for flag in args.ssh_flag
        ]

      if len(instance_refs) > 1:
        thread = threading.Thread(
            target=_RunComputeSshForInstance,
            args=(
                compute_ssh_cmd,
                instance_args,
                instance_ref.Name(),
                idx,
                exit_statuses,
                output_directory_path,
            ),
        )
        ssh_threads.append(thread)
        thread.start()
        current_batch_size += 1
        if current_batch_size == batch_size:
          _WaitForBatchCompletion(ssh_threads)
          current_batch_size = 0
          ssh_threads = []
          if any(exit_statuses):
            break
      else:
        _RunComputeSshForInstance(
            compute_ssh_cmd,
            instance_args,
            instance_ref.Name(),
            idx,
            exit_statuses,
            output_directory_path,
        )

    if ssh_threads:
      _WaitForBatchCompletion(ssh_threads)

  _PrintExecutionSummary(instance_refs, exit_statuses, batch_size)
  for status in exit_statuses:
    if status:
      sys.exit(status)
