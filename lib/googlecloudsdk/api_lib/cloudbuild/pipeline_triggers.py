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
"""Requests and response hooks for Cloud Build Pipeline Triggers."""

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import pipeline_trigger_config
from googlecloudsdk.core import log


def Apply(client, trigger_name, trigger, validate_only=False):
  """Creates or updates a pipeline trigger with a single upsert request.

  The request always carries the full update mask, so the stored trigger ends
  up exactly as the definition describes it.

  Args:
    client: apitools client for the Cloud Build v1 API.
    trigger_name: str, the full resource name of the trigger.
    trigger: messages.PipelineTrigger, the definition to store.
    validate_only: bool, whether to validate the request without storing it.

  Returns:
    messages.Operation, the long-running operation for the upsert.
  """
  messages = client.MESSAGES_MODULE
  request = messages.CloudbuildProjectsLocationsPipelinesTriggersPatchRequest(
      name=trigger_name,
      pipelineTrigger=trigger,
      updateMask=pipeline_trigger_config.FULL_UPDATE_MASK,
      allowMissing=True,
      validateOnly=validate_only,
  )
  return client.projects_locations_pipelines_triggers.Patch(request)


def ApplyFromHook(unused_ref, args):
  """Issue-request hook for `gcloud builds pipelines triggers apply`."""
  track = args.calliope_command.ReleaseTrack()
  messages = cloudbuild_util.GetMessagesModule(track)

  # Load the definition before resolving the resource, so that a missing or
  # malformed file is reported as such. The trigger ID falls through to this
  # same file, which would otherwise turn a typo in --file into a complaint
  # about an unspecified trigger.
  trigger = pipeline_trigger_config.LoadTriggerConfigFromPath(
      args.file, messages
  )

  trigger_ref = args.CONCEPTS.trigger.Parse()
  trigger_name = trigger_ref.RelativeName()
  client = cloudbuild_util.GetClientInstance(
      track, location=trigger_ref.locationsId
  )

  op = Apply(client, trigger_name, trigger, validate_only=args.dry_run)
  if not args.dry_run:
    log.status.Print(
        'Apply request issued for pipeline trigger [{}].'.format(trigger_name)
    )
  return op


def LogApplySuccess(response, args):
  """Modify-response hook for `gcloud builds pipelines triggers apply`."""
  if args.async_:
    return response
  trigger_name = args.CONCEPTS.trigger.Parse().RelativeName()
  if args.dry_run:
    log.status.Print(
        'Dry run validated pipeline trigger [{}].'.format(trigger_name)
    )
  else:
    log.status.Print('Applied pipeline trigger [{}].'.format(trigger_name))
  return response
