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
"""Command to create or update a Cloud Build Pipeline declaratively."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import pipeline_config
from googlecloudsdk.api_lib.cloudbuild import pipeline_trigger_config
from googlecloudsdk.api_lib.cloudbuild import pipeline_triggers
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import pipeline_flags
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_TRIGGER_APPLY_TIMEOUT_MS = 180000


class TriggerApplyError(core_exceptions.Error):
  """One or more nested pipeline triggers failed to apply."""

_DETAILED_HELP = {
    'DESCRIPTION': (
        """\
        {description}

        The definition file may also declare the pipeline's triggers inline,
        in a `triggers` list next to the pipeline fields. Each entry takes the
        same form as a `{parent_command} triggers apply` definition and
        must have a `name`, which becomes its trigger ID:

          name: payments-pipeline
          displayName: Payments pipeline
          triggers:
            - name: deploy-main
              gitRepositoryLink: projects/my-project/locations/us-central1/connections/github/gitRepositoryLinks/payments
              branchPush:
                gitRef:
                  nameRegexes:
                    - ^main$

        The pipeline is applied first, then each listed trigger in file order.
        A listed trigger is fully replaced by its definition. Triggers that
        the file does not list are left untouched; delete them with
        `{parent_command} triggers delete`. If a trigger fails to apply, the
        remaining triggers are still applied, and the command then exits with
        an error that names every trigger that failed.
        """
    ),
    'EXAMPLES': (
        """\
        To apply a pipeline defined in `pipeline.yaml` in region `us-central1`:

          $ {command} --file=pipeline.yaml --region=us-central1

        To apply a pipeline with an explicit ID and service account:

          $ {command} main-pipeline --file=pipeline.yaml --region=us-central1 \\
              --service-account=cb-sa@my-project.iam.gserviceaccount.com

        To validate a pipeline definition without persisting changes:

          $ {command} --file=pipeline.yaml --region=us-central1 --dry-run
        """
    ),
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class Apply(base.CreateCommand):
  """Create or update a Cloud Build Pipeline declaratively."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    pipeline_flags.AddPipelineApplyFlags(parser)

  def Run(self, args):
    """Executes the `apply` command."""
    track = self.ReleaseTrack()
    messages = cloudbuild_util.GetMessagesModule(track)

    # Load the definition before resolving the resource, so that a missing or
    # malformed file is reported as such. The pipeline ID falls through to
    # this same file, which would otherwise turn a typo in --file into a
    # complaint about an unspecified pipeline.
    config = pipeline_config.LoadPipelineConfigFromPath(args.file, messages)
    pipeline = config.pipeline

    # Nested triggers are converted up front, so that a bad trigger definition
    # stops the command before its first request rather than after the
    # pipeline has already been written.
    triggers = pipeline_trigger_config.LoadNestedTriggers(
        config.triggers, messages, args.file
    )

    pipeline_ref = args.CONCEPTS.pipeline.Parse()
    pipeline_name = pipeline_ref.RelativeName()
    client = cloudbuild_util.GetClientInstance(
        track, location=pipeline_ref.locationsId
    )

    if args.IsSpecified('display_name'):
      pipeline.displayName = args.display_name
    if args.IsSpecified('service_account'):
      pipeline.serviceAccount = args.service_account

    mask = pipeline_config.ComputeUpdateMask(pipeline)
    req = messages.CloudbuildProjectsLocationsPipelinesPatchRequest(
        name=pipeline_name,
        pipeline=pipeline,
        updateMask=mask,
        allowMissing=True,
        validateOnly=args.dry_run,
    )
    op = client.projects_locations_pipelines.Patch(req)

    if args.dry_run:
      log.status.Print(
          'Dry run validated pipeline [{}].'.format(pipeline_name)
      )
      if triggers:
        _DryRunTriggers(client, pipeline_ref, triggers)
      return None

    op_resource = resources.REGISTRY.ParseRelativeName(
        op.name, collection='cloudbuild.projects.locations.operations'
    )
    poller = waiter.CloudOperationPoller(
        client.projects_locations_pipelines,
        client.projects_locations_operations,
    )
    result = waiter.WaitFor(
        poller, op_resource, 'Applying pipeline', max_wait_ms=3600000
    )
    log.status.Print('Applied pipeline [{}].'.format(pipeline_name))

    # The triggers are children of the pipeline, so they can only be written
    # once the pipeline operation above has finished.
    if triggers:
      _ApplyTriggers(client, pipeline_name, triggers, dry_run=False)
    return result


def _DryRunTriggers(client, pipeline_ref, triggers):
  """Validates the nested triggers on the server, if their parent exists.

  The server cannot validate a trigger whose parent pipeline does not exist
  yet, even with `validateOnly`, and a dry run never creates the parent. In
  that case the triggers have only had the local checks that converting them
  already performed, which is reported as a warning.

  Args:
    client: apitools client for the Cloud Build v1 API.
    pipeline_ref: resources.Resource, the parent pipeline.
    triggers: [(str, messages.PipelineTrigger)], the nested triggers.

  Raises:
    TriggerApplyError: If any trigger failed server-side validation.
  """
  pipeline_name = pipeline_ref.RelativeName()
  messages = client.MESSAGES_MODULE
  try:
    client.projects_locations_pipelines.Get(
        messages.CloudbuildProjectsLocationsPipelinesGetRequest(
            name=pipeline_name
        )
    )
  except apitools_exceptions.HttpNotFoundError:
    log.warning(
        'Pipeline [{}] does not exist yet, so triggers [{}] were only checked'
        ' locally. The server checks them when you apply without --dry-run.'
        .format(
            pipeline_ref.pipelinesId,
            ', '.join(trigger_id for trigger_id, _ in triggers),
        )
    )
    return
  _ApplyTriggers(client, pipeline_name, triggers, dry_run=True)


def _ApplyTriggers(client, pipeline_name, triggers, dry_run):
  """Applies the nested triggers one at a time, in file order.

  A trigger that fails does not stop the others: every trigger that can be
  applied is, and the failures are reported together at the end. Re-running
  the command then retries only what is still wrong, since each call is an
  idempotent upsert.

  Args:
    client: apitools client for the Cloud Build v1 API.
    pipeline_name: str, the full resource name of the parent pipeline.
    triggers: [(str, messages.PipelineTrigger)], the nested triggers.
    dry_run: bool, whether to validate the triggers instead of applying them.

  Raises:
    TriggerApplyError: If any trigger failed, naming each one.
  """
  verb = 'Dry run validated' if dry_run else 'Applied'
  poller = waiter.CloudOperationPollerNoResources(
      client.projects_locations_operations,
  )
  failures = []
  for trigger_id, trigger in triggers:
    trigger_name = '{}/triggers/{}'.format(pipeline_name, trigger_id)
    try:
      op = pipeline_triggers.Apply(
          client, trigger_name, trigger, validate_only=dry_run
      )
      if not dry_run:
        op_resource = resources.REGISTRY.ParseRelativeName(
            op.name, collection='cloudbuild.projects.locations.operations'
        )
        waiter.WaitFor(
            poller,
            op_resource,
            'Applying pipeline trigger [{}]'.format(trigger_id),
            max_wait_ms=_TRIGGER_APPLY_TIMEOUT_MS,
        )
    except apitools_exceptions.HttpError as e:
      failures.append((trigger_id, str(api_exceptions.HttpException(e))))
      continue
    except (waiter.OperationError, waiter.TimeoutError) as e:
      failures.append((trigger_id, str(e)))
      continue
    log.status.Print('{} pipeline trigger [{}].'.format(verb, trigger_name))

  if failures:
    raise TriggerApplyError(
        '{} the pipeline and {} of {} triggers. Failed triggers:\n{}'.format(
            verb,
            len(triggers) - len(failures),
            len(triggers),
            '\n'.join(
                '  {}: {}'.format(trigger_id, message)
                for trigger_id, message in failures
            ),
        )
    )
