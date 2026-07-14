# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command for running jobs."""

import copy
import subprocess
import time

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import container_parser
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import messages_util
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.run import streaming
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker


def ContainerOverridesGroup():
  """Returns an argument group with all per-container args for overrides."""

  help_text = """
Container Flags

  If the --container is specified the following arguments may only be specified after a --container flag.
"""
  group = base.ArgumentGroup(help=help_text)
  group.AddArgument(flags.ArgsFlag(for_execution_overrides=True))
  group.AddArgument(flags.OverrideEnvVarsFlag())
  return group


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Execute(base.Command):
  """Execute a job."""

  detailed_help = {
      'DESCRIPTION': (
          """
          {description}
          """
      ),
      'EXAMPLES': (
          """
          To execute a job:

              $ {command} my-job
          """
      ),
  }

  container_flags_text = '`--update-env-vars`, `--args`'

  @classmethod
  def CommonArgs(cls, parser):
    job_presentation = presentation_specs.ResourcePresentationSpec(
        'JOB',
        resource_args.GetJobResourceSpec(prompt=True),
        'Job to execute.',
        required=True,
        prefixes=False,
    )
    concept_parsers.ConceptParser([job_presentation]).AddToParser(parser)
    polling_group = parser.add_mutually_exclusive_group()
    flags.AddAsyncFlag(polling_group)
    flags.AddWaitForCompletionFlag(polling_group)
    if cls.ReleaseTrack() in (base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA):
      polling_group.add_argument(
          '--tail',
          action='store_true',
          default=False,
          help='Tail logs after launching the execution.',
      )
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')
    flags.AddTaskTimeoutFlags(parser, for_execution_overrides=True)
    flags.AddTasksFlag(parser, for_execution_overrides=True)

  @staticmethod
  def Args(parser):
    Execute.CommonArgs(parser)
    container_args = ContainerOverridesGroup()
    container_parser.AddContainerFlags(parser, container_args)

  def _MakeContainerOverrde(self, operations, args, container_name=None):
    # If args list has been explicitly set as an empty list,
    # this is to clear out the existing args list.
    clear_args = flags.FlagIsExplicitlySet(args, 'args') and not args.args
    return operations.MakeContainerOverride(
        name=container_name,
        update_env_vars=args.update_env_vars,
        args=args.args,
        clear_args=clear_args,
    )

  def _AssertContainerOverrides(self, args):
    if flags.FlagIsExplicitlySet(args, 'containers'):
      for container_name, container_args in args.containers.items():
        if not flags.FlagIsExplicitlySet(
            container_args, 'args'
        ) and not flags.FlagIsExplicitlySet(container_args, 'update_env_vars'):
          raise exceptions.NoConfigurationChangeError(
              'No container overrides requested to container `{}`. '
              'Did you mean to include the flags {} after `--container` flag?'
              .format(container_name, self.container_flags_text)
          )

  def Run(self, args):
    """Execute a Job on Cloud Run."""
    job_ref = args.CONCEPTS.job.Parse()
    flags.ValidateResource(job_ref)
    self._AssertContainerOverrides(args)
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    with serverless_operations.Connect(conn_context) as operations:
      with progress_tracker.StagedProgressTracker(
          'Creating execution...',
          stages.ExecutionStages(include_completion=args.wait),
          failure_message='Executing job failed',
          suppress_output=args.async_,
      ) as tracker:
        overrides = None
        if flags.HasExecutionOverrides(args):
          operations.ValidateConfigOverrides(
              job_ref, flags.GetExecutionOverridesChangesForValidation(args)
          )
          container_overrides = []
          if flags.HasContainerOverrides(args):
            if flags.HasTopLevelContainerOverride(args):
              container_overrides.append(
                  self._MakeContainerOverrde(operations, args)
              )
            if flags.FlagIsExplicitlySet(args, 'containers'):
              for container_name, container_args in args.containers.items():
                container_overrides.append(
                    self._MakeContainerOverrde(
                        operations, container_args, container_name
                    )
                )
          delay_execution = (
              args.delay_execution
              if flags.FlagIsExplicitlySet(args, 'delay_execution')
              else None
          )
          overrides = operations.GetExecutionOverrides(
              args.tasks,
              args.task_timeout,
              delay_execution,
              container_overrides,
          )
        e = operations.RunJob(
            job_ref,
            tracker,
            args.wait,
            args.async_,
            self.ReleaseTrack(),
            overrides,
        )

      if getattr(args, 'tail', False):
        e = self._TailLogs(operations, job_ref, e, args)
        pretty_print.Success(
            'Execution [{{bold}}{execution}{{reset}}] has '
            'successfully completed.'.format(execution=e.name)
        )
        log.status.Print(
            messages_util.GetExecutionCreatedMessage(self.ReleaseTrack(), e)
        )
        return e

      if args.async_:
        pretty_print.Success(
            'Execution [{{bold}}{execution}{{reset}}] is being'
            ' started asynchronously.'.format(execution=e.name)
        )
      else:
        operation = 'completed' if args.wait else 'started running'

        pretty_print.Success(
            'Execution [{{bold}}{execution}{{reset}}] has '
            'successfully {operation}.'.format(
                execution=e.name, operation=operation
            )
        )

      log.status.Print(
          messages_util.GetExecutionCreatedMessage(self.ReleaseTrack(), e)
      )
      return e

  def _TailLogs(self, operations, job_ref, e, args):
    """Tail logs for the execution and wait for it to complete."""
    region = flags.GetRegion(args)
    project_id = properties.VALUES.core.project.Get(required=True)

    filters = []
    filters.append('resource.type=%s' % 'cloud_run_job')
    filters.append(
        # gcloud-disable-gdu-domain
        'labels."run.googleapis.com/execution_name"=%s'
        % e.name
    )
    filters.append('resource.labels.location=%s' % region)
    filters.append('severity>=DEFAULT')
    filter_str = ' '.join(filters)

    wrapper = streaming.LogStreamingWrapper()
    log_executable = wrapper.executable
    log_args = [
        log_executable,
        '-projectId',
        project_id,
        '-filter',
        filter_str,
        '-format',
        'run',
    ]

    log.status.Print('Tailing logs for execution [{}]...'.format(e.name))

    env = execution_utils.GetToolEnv()
    log_proc = subprocess.Popen(log_args, env=env)

    execution_ref = resources.REGISTRY.Parse(
        e.name,
        params={'namespacesId': e.namespace},
        collection='run.namespaces.executions',
    )

    is_completed = False
    final_execution = e
    try:
      while not is_completed:
        time.sleep(2)
        if log_proc.poll() is not None:
          log.debug(
              'Log streaming process finished with code {}'.format(
                  log_proc.returncode
              )
          )
        final_execution = operations.GetExecution(execution_ref)
        conditions = final_execution.conditions
        if conditions and conditions.IsTerminal():
          is_completed = True
    finally:
      if log_proc.poll() is None:
        log_proc.terminate()
        log_proc.wait()

    if final_execution.conditions.IsFailed():
      raise exceptions.ExecutionFailedError(
          'The execution failed.'
          + messages_util.GetExecutionCreatedMessage(
              self.ReleaseTrack(), final_execution
          )
      )

    return final_execution


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.RegionalEndpointsSupported
class BetaExecute(Execute):
  """Execute a job."""

  detailed_help = copy.deepcopy(Execute.detailed_help)

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)
    container_args = ContainerOverridesGroup()
    container_parser.AddContainerFlags(
        parser, container_args, cls.ReleaseTrack()
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaExecute(BetaExecute):
  """Execute a job."""

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)
    flags.AddDelayExecutionFlag(parser)
    container_args = ContainerOverridesGroup()
    container_parser.AddContainerFlags(
        parser, container_args, cls.ReleaseTrack()
    )
