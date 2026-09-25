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
"""Common utilities for Agent Registry commands."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files
from googlecloudsdk.generated_clients.apis.agentregistry.v1alpha import agentregistry_v1alpha_messages as ar_messages


def SetDisplayNameAndDefaultsInCreate(resource_ref, args, request_msg):
  """Sets default values for displayName, type, and targetState if not provided.

  Ensures the request body is never empty and fulfills backend requirements
  even when optional flags are omitted.

  Args:
    resource_ref: The resource reference.
    args: The command line arguments.
    request_msg: The request message to modify.

  Returns:
    The modified request message.
  """
  del args  # Unused
  messages = apis.GetMessagesModule('agentregistry', 'v1alpha')
  skill = request_msg.skill
  if not skill:
    skill_class = getattr(messages, 'Skill')
    skill = skill_class()
    request_msg.skill = skill

  if resource_ref:
    if not request_msg.skillId:
      request_msg.skillId = resource_ref.Name()
    request_msg.parent = 'projects/{}/locations/{}'.format(
        resource_ref.projectsId, resource_ref.locationsId
    )

  # Fallback displayName
  if not skill.displayName:
    skill_id = request_msg.skillId or (
        resource_ref.skillsId if resource_ref else 'my-skill'
    )
    skill.displayName = skill_id

  skill_class = getattr(messages, 'Skill')
  # Fallback type
  if not skill.type:
    skill.type = skill_class.TypeValueValuesEnum.SIMPLE

  # Fallback targetState
  if not skill.targetState:
    skill.targetState = (
        skill_class.TargetStateValueValuesEnum.TARGET_STATE_DRAFT
    )

  return request_msg


def ReadPayloadFile(resource_ref, args, request_msg):
  """Reads the binary payload file (ZIP) and attaches it to the request message."""
  del resource_ref  # Unused
  if getattr(args, 'payload', None):
    content = files.ReadBinaryFileContents(args.payload)

    messages = apis.GetMessagesModule('agentregistry', 'v1alpha')

    if not request_msg.skillRevision:
      skill_revision_class = getattr(messages, 'SkillRevision')
      request_msg.skillRevision = skill_revision_class()

    archive_upload_source_class = getattr(messages, 'ArchiveUploadSource')
    archive_upload_source = archive_upload_source_class(archiveContent=content)
    request_msg.skillRevision.archiveUploadSource = archive_upload_source

  return request_msg


def SkillDisplayNameHook(resource_ref, args):
  """Modifies the display name of the skill to include the correct prefix.

  Ensures that standard gcloud console output reflects the actual backend
  resource name. The input `resource_ref.Name()` is the name typed by the user,
  which may or may not already have the prefix (e.g. 'my-skill' or
  'private-my-skill').

  This hook prepends the publisher prefix (or 'private-') to the skill name.

  Args:
    resource_ref: The resource reference.
    args: The command line arguments.

  Returns:
    The display name string.
  """
  if not resource_ref:
    return 'unknown'

  name = resource_ref.Name()
  prefix = (
      args.publisher.split('/')[-1]
      if args and args.IsSpecified('publisher')
      else 'private'
  )
  return f'{prefix}-{name}'


_SkillsPatchRequest = (
    ar_messages.AgentregistryProjectsLocationsSkillsPatchRequest
)


def SetUpdateMaskInUpdate(
    resource_ref: resources.Resource | None,
    args: parser_extensions.Namespace,
    request_msg: _SkillsPatchRequest,
) -> _SkillsPatchRequest:
  """Normalizes updateMask for skills update, replacing sub-field paths.

  Replaces sub-field paths like scanningConfig.policy with scanning_config or
  scanningConfig so backend update validation succeeds.

  Args:
    resource_ref: The resource reference.
    args: The command line arguments.
    request_msg: The request message to modify.

  Returns:
    The modified request message.
  """
  del resource_ref, args
  if request_msg.updateMask:
    paths = [p.strip() for p in request_msg.updateMask.split(',')]
    normalized_paths = []
    for p in paths:
      if p in (
          'scanningConfig.policy',
          'scanningConfig',
          'scanning_config.policy',
          'scanning_config',
      ):
        if (
            'scanningConfig' not in normalized_paths
            and 'scanning_config' not in normalized_paths
        ):
          normalized_paths.append('scanningConfig')
      else:
        normalized_paths.append(p)
    request_msg.updateMask = ','.join(normalized_paths)
  return request_msg

