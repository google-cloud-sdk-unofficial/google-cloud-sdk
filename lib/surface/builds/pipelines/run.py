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
"""Command to trigger an execution of a Cloud Build Pipeline."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import pipeline_logs
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import execution
from googlecloudsdk.command_lib.cloudbuild import pipeline_flags
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


_PIPELINE_RUN_TABLE_FORMAT = (
    'table(\n'
    '  name.segment(-1):label=RUN_ID,\n'
    '  pipeline.segment(-1):label=PIPELINE,\n'
    '  state:label=STATE,\n'
    '  startTime.date(undefined="-"):label=START_TIME,\n'
    '  duration(start=startTime,end=finishTime,precision=0,calendar=false,'
    'undefined="  -").slice(2:).join(""):label=DURATION\n'
    ')'
)


def _EncodeInputParams(params, messages):
  """Encodes `--params` key-value pairs into PipelineRun.InputParamsValue.

  Args:
    params: Mapping of parameter names to override values from `--params`, or
      None when `--params` is omitted.
    messages: Apitools messages module for the Cloud Build v1 API.

  Returns:
    A `PipelineRun.InputParamsValue` message containing the sorted parameter
    entries, or None if `params` is empty or None.
  """
  if not params:
    return None
  additional_properties = [
      messages.PipelineRun.InputParamsValue.AdditionalProperty(
          key=key, value=value
      )
      for key, value in sorted(params.items())
  ]
  return messages.PipelineRun.InputParamsValue(
      additionalProperties=additional_properties
  )


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class Run(base.CreateCommand):
  """Trigger an execution of a Cloud Build Pipeline."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Trigger an execution (pipeline run) of a Cloud Build Pipeline.

          By default, this command waits for the pipeline run to complete,
          renders a live stage and step progress tree, automatically displays
          logs for any failed stages, and prints the final `PipelineRun` summary
          table. Use `--stream-logs` to stream live container logs from all
          active stages, or `--async` to return the created `PipelineRun`
          immediately without waiting for stages to complete.
          """
      ),
      'EXAMPLES': (
          'To run a pipeline named `main-pipeline` in region `us-central1` and '
          'watch live DAG progress:\n\n'
          '  $ {command} main-pipeline --region=us-central1\n\n'
          'To run a pipeline and stream live container logs across all stages:'
          '\n\n'
          '  $ {command} main-pipeline --region=us-central1 --stream-logs\n\n'
          'To run a pipeline with parameter overrides without waiting for '
          'completion:\n\n'
          '  $ {command} main-pipeline --region=us-central1 '
          '--params=ENV=staging,IMAGE_TAG=v1.2.0 --async\n'
      ),
  }

  @staticmethod
  def Args(parser):
    """Registers flags for this command.

    Args:
      parser: The argparse parser used to register command arguments.
    """
    pipeline_flags.AddPipelineRunFlags(parser)
    parser.display_info.AddFormat(_PIPELINE_RUN_TABLE_FORMAT)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """Executes the `pipelines run` command.

    Args:
      args: Parsed command-line arguments namespace.

    Returns:
      The created `PipelineRun` message immediately when `--async` is set, or
      the final `PipelineRun` message after watching execution complete.

    Raises:
      waiter.OperationError: If the CreatePipelineRun long-running operation
        fails.
    """
    pipeline_ref = args.CONCEPTS.pipeline.Parse()
    client = cloudbuild_util.GetClientInstance(
        self.ReleaseTrack(), location=pipeline_ref.locationsId
    )
    messages = client.MESSAGES_MODULE

    parent = 'projects/{project}/locations/{location}'.format(
        project=pipeline_ref.projectsId,
        location=pipeline_ref.locationsId,
    )
    pipeline_run_message = messages.PipelineRun(
        pipeline=pipeline_ref.RelativeName(),
        inputParams=_EncodeInputParams(args.params, messages),
    )
    create_request = (
        messages.CloudbuildProjectsLocationsPipelineRunsCreateRequest(
            parent=parent,
            pipelineRun=pipeline_run_message,
        )
    )

    operation = client.projects_locations_pipelineRuns.Create(create_request)
    log.status.Print(
        'Run request issued for: [{}]'.format(pipeline_ref.Name())
    )

    if not operation.done:
      operation_ref = resources.REGISTRY.ParseRelativeName(
          operation.name,
          collection='cloudbuild.projects.locations.operations',
      )
      poller = waiter.CloudOperationPollerNoResources(
          client.projects_locations_operations
      )
      operation_response = waiter.WaitFor(
          poller,
          operation_ref,
          'Waiting for operation [{}] to complete'.format(operation.name),
      )
    else:
      if operation.error:
        raise waiter.OperationError(operation.error.message)
      operation_response = operation.response

    pipeline_run = encoding.PyValueToMessage(
        messages.PipelineRun, encoding.MessageToPyValue(operation_response)
    )

    run_ref = resources.REGISTRY.ParseRelativeName(
        pipeline_run.name,
        collection='cloudbuild.projects.locations.pipelineRuns',
    )
    log.CreatedResource(run_ref)
    if properties.IsDefaultUniverse():
      console_url = (
          'https://console.cloud.google.com/cloud-build/pipeline-runs/detail/'
          '{region}/{run_id}?project={project}'
      ).format(
          region=run_ref.locationsId,
          run_id=run_ref.Name(),
          project=run_ref.projectsId,
      )
      log.status.Print('Logs are available at [{}].'.format(console_url))

    if args.async_:
      return pipeline_run

    watcher = pipeline_logs.PipelineRunWatcher(
        client=client,
        messages=messages,
        pipeline_run_ref=run_ref,
        stream_logs=args.stream_logs,
    )
    cancel_handler = execution.MashHandler(
        execution.GetCancelPipelineRunHandler(watcher)
    )
    with execution_utils.CtrlCSection(cancel_handler):
      pipeline_run = watcher.Watch(initial_run=pipeline_run)

    if watcher.cancelled:
      self.exit_code = 1
    elif (
        pipeline_run.state
        != messages.PipelineRun.StateValueValuesEnum.SUCCEEDED
    ):
      if pipeline_run.failureInfo and pipeline_run.failureInfo.detail:
        log.status.Print(
            '\nBUILD FAILURE: {}'.format(pipeline_run.failureInfo.detail)
        )
      else:
        log.status.Print(
            '\nBUILD FAILURE: PipelineRun [{}] finished with state {}.'.format(
                pipeline_run.name, pipeline_run.state
            )
        )
      self.exit_code = 1

    return pipeline_run
