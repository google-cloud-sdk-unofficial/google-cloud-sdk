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
"""Command to deploy an agent runtime in Vertex AI."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.agent_runtimes import client
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.ai.agent_runtimes import agent_runtimes_util
from googlecloudsdk.command_lib.ai.agent_runtimes import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _ValidateCreateArgs(args):
  """Validates flags when deploying a new agent runtime."""
  if not args.display_name:
    raise gcloud_exceptions.RequiredArgumentException(
        '--display-name',
        'The --display-name flag is required when creating a new agent'
        ' runtime.',
    )
  validation.ValidateDisplayName(args.display_name)
  if not args.image and not args.source:
    raise gcloud_exceptions.OneOfArgumentsRequiredException(
        ['--image', '--source'],
        'Exactly one of [--image, --source] must be specified when creating a'
        ' new agent runtime.',
    )
  update_only_flags = (
      ('--etag', args.etag),
      ('--traffic-split-to-revisions', args.traffic_split_to_revisions),
      ('--traffic-split-always-latest', args.traffic_split_always_latest),
      ('--update-env-vars', args.update_env_vars),
      ('--remove-env-vars', args.remove_env_vars),
      ('--clear-env-vars', args.clear_env_vars),
      ('--update-secret-env-vars', args.update_secret_env_vars),
      ('--remove-secret-env-vars', args.remove_secret_env_vars),
      ('--clear-secret-env-vars', args.clear_secret_env_vars),
      ('--update-labels', args.update_labels),
      ('--remove-labels', args.remove_labels),
      ('--clear-labels', args.clear_labels),
  )
  for flag_name, flag_value in update_only_flags:
    if flag_value:
      raise gcloud_exceptions.InvalidArgumentException(
          flag_name,
          'The {} flag only applies when updating an existing agent'
          ' runtime.'.format(flag_name),
      )


def _ValidateUpdateArgs(args):
  """Validates flags when updating an existing agent runtime."""
  if args.kms_key_name:
    raise gcloud_exceptions.InvalidArgumentException(
        '--kms-key-name',
        'The --kms-key-name flag only applies when creating a new agent'
        ' runtime.',
    )
  if args.IsSpecified('labels'):
    raise gcloud_exceptions.InvalidArgumentException(
        '--labels',
        'The --labels flag only applies when creating a new agent'
        ' runtime. Use --update-labels, --remove-labels, or --clear-labels to'
        ' modify labels of an existing runtime.',
    )
  if args.display_name:
    validation.ValidateDisplayName(args.display_name)
  if args.traffic_split_to_revisions:
    targets = args.traffic_split_to_revisions
    for rev, pct in targets.items():
      if pct < 0:
        raise gcloud_exceptions.InvalidArgumentException(
            '--traffic-split-to-revisions',
            'Traffic percentage for [{}] must be non-negative, got'
            ' [{}].'.format(rev, pct),
        )
    total = sum(targets.values())
    if total != 100:
      raise gcloud_exceptions.InvalidArgumentException(
          '--traffic-split-to-revisions',
          'The sum of all traffic split percentages must be 100, got'
          ' [{}].'.format(total),
      )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class Deploy(base.SilentCommand):
  """Create or update an Agent Runtime and trigger a deployment.

  If RUNTIME is provided, the existing runtime is updated; otherwise a new
  runtime is created.

  When creating a new runtime (RUNTIME is not provided), `--display-name` and
  either `--image` or `--source` are required. When
  updating an existing runtime (RUNTIME is provided), `--image` and `--source`
  are optional if updating other configuration settings.

  ## EXAMPLES

  To deploy a new agent runtime from a container image, run:

    $ {command} --display-name="My agent"
    --image=us-docker.pkg.dev/example/my-agent:latest --region=us-central1

  To deploy a new agent runtime from local source code, run:

    $ {command} --display-name="My agent" --source=./my-agent
    --entrypoint-module=my_agent.agent --region=us-central1

  To update an existing agent runtime with a new container image, run:

    $ {command} 123456789 --region=us-central1
    --image=us-docker.pkg.dev/example/my-agent:v2
  """

  @staticmethod
  def Args(parser):
    flags.AddDeployFlags(parser)

  def Run(self, args):
    runtime_ref = args.CONCEPTS.runtime.Parse()
    if runtime_ref is None:
      return self._Create(args)
    return self._Update(args, runtime_ref)

  def _Create(self, args):
    """Creates a new agent runtime."""
    _ValidateCreateArgs(args)
    region_ref = args.CONCEPTS.region.Parse()
    return agent_runtimes_util.CreateRuntime(
        region_ref, args, self.ReleaseTrack(), asynchronous=False
    )

  def _Update(self, args, runtime_ref):
    """Updates an existing agent runtime."""
    _ValidateUpdateArgs(args)
    region = runtime_ref.locationsId
    agent_runtimes_util.ValidateRegion(region)

    with endpoint_util.AiplatformEndpointOverrides(
        constants.BETA_VERSION, region=region
    ):
      runtimes_client = client.AgentRuntimesClient(
          version=constants.BETA_VERSION
      )
      try:
        existing_runtime = runtimes_client.Get(runtime_ref.RelativeName())
      except apitools_exceptions.HttpError as error:
        raise api_exceptions.HttpException(
            error,
            'ResponseError: code={status_code}, message={status_message}',
        )
      agent_runtime = agent_runtimes_util.AgentRuntimeBuilder(
          runtimes_client
      ).BuildForUpdate(args, existing_runtime=existing_runtime)
      labels_diff = labels_util.Diff.FromUpdateArgs(args)
      has_labels_update = (
          labels_diff.MayHaveUpdates() and agent_runtime.labels is not None
      )
      update_mask_paths = agent_runtimes_util.GetUpdateMaskPaths(
          args, has_labels_update=has_labels_update
      )
      update_mask = (
          ','.join(update_mask_paths) if update_mask_paths else None
      )
      try:
        operation = runtimes_client.Update(
            runtime_ref.RelativeName(),
            agent_runtime,
            update_mask=update_mask,
        )
      except apitools_exceptions.HttpError as error:
        raise api_exceptions.HttpException(
            error,
            'ResponseError: code={status_code}, message={status_message}',
        )
      response = operations_util.WaitForOpMaybe(
          operations_client=operations.OperationsClient(),
          op=operation,
          op_ref=agent_runtimes_util.ParseOperation(operation.name),
          asynchronous=False,
          message='Waiting for the agent runtime to be updated...',
      )
      log.UpdatedResource(runtime_ref.reasoningEnginesId, kind='agent runtime')
      return response
