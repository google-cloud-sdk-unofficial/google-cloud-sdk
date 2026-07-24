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
from googlecloudsdk.core.util import files


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

  # Fallback displayName
  if not skill.displayName:
    skill_id = getattr(request_msg, 'skillId', None) or (
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
  """Modifies the display name of the skill to include the 'private-' prefix.

  Ensures that standard gcloud console output reflects the actual backend
  resource name, even if the user didn't type the prefix.

  Args:
    resource_ref: The resource reference.
    args: The command line arguments.

  Returns:
    The display name string.
  """
  del args  # Unused
  if not resource_ref:
    return 'unknown'

  name = resource_ref.Name()
  if not name.startswith('private-'):
    name = 'private-' + name

  return name


def StripPrivatePrefixHook(ref, args, request):
  """Strips 'private-' prefix from skillId in the request path/ID.

  Prevents potential double-prefixing if the user explicitly typed the
  prefix in the command, ensuring we send the raw ID to the backend which
  then applies the enforcement.

  Args:
    ref: The resource reference.
    args: The command line arguments.
    request: The request message to modify.

  Returns:
    The modified request message.
  """
  del ref, args  # Unused

  if request.skillId:
    while request.skillId.startswith('private-'):
      request.skillId = request.skillId[len('private-') :]

  return request


def EnsurePrivatePrefixInResponseHook(response, args):
  """Ensures the response returned by operations or get has the correct name.

  Guarantees that the resource name in the response starts with 'private-' for
  skill resources, ensuring consistent display in gcloud.

  Args:
    response: The response message.
    args: The command line arguments.

  Returns:
    The modified response message.
  """
  del args  # Unused

  if response and hasattr(response, 'name') and response.name:
    parts = response.name.split('/')
    if len(parts) == 6 and parts[4] == 'skills':
      if not parts[5].startswith('private-'):
        parts[5] = 'private-' + parts[5]
        response.name = '/'.join(parts)

  return response
