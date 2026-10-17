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
"""Utilities and flag helpers for Dataflow ConfigStore settings commands."""

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs

_PROJECT_SETTING_COLLECTION = 'dataflow.projects.locations.configStoreSettings'
_FOLDER_SETTING_COLLECTION = 'dataflow.folders.locations.configStoreSettings'
_ORG_SETTING_COLLECTION = 'dataflow.organizations.locations.configStoreSettings'

# Multitype concept type names. Commands dispatch on the parsed concept type,
# so these must match the `resource_name` of each resource spec below.
PROJECT_SETTING = 'project_setting'
FOLDER_SETTING = 'folder_setting'
ORG_SETTING = 'org_setting'

# Placeholder setting ID used by commands `list`. It is never sent to the
# API: those commands only use `GetParentRelativeName` on the parsed reference.
_UNUSED_SETTING_ID = '-'


_LOCATION_HELP_TEXT = (
    'The location of the ConfigStore setting (e.g. us-central1).'
)
_SETTING_ID_HELP_TEXT = 'The ConfigStore setting ID.'


def _ProjectSettingResourceSpec(setting_id_config):
  return concepts.ResourceSpec(
      _PROJECT_SETTING_COLLECTION,
      resource_name=PROJECT_SETTING,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=concepts.ResourceParameterAttributeConfig(
          name='location', help_text=_LOCATION_HELP_TEXT,
      ),
      configStoreSettingsId=setting_id_config,
  )


def _FolderSettingResourceSpec(setting_id_config):
  return concepts.ResourceSpec(
      _FOLDER_SETTING_COLLECTION,
      resource_name=FOLDER_SETTING,
      foldersId=concepts.ResourceParameterAttributeConfig(
          name='folder', help_text='The Google Cloud folder ID.'
      ),
      locationsId=concepts.ResourceParameterAttributeConfig(
          name='location', help_text=_LOCATION_HELP_TEXT,
      ),
      configStoreSettingsId=setting_id_config,
  )


def _OrgSettingResourceSpec(setting_id_config):
  return concepts.ResourceSpec(
      _ORG_SETTING_COLLECTION,
      resource_name=ORG_SETTING,
      organizationsId=concepts.ResourceParameterAttributeConfig(
          name='organization', help_text='The Google Cloud organization ID.'
      ),
      locationsId=concepts.ResourceParameterAttributeConfig(
          name='location', help_text=_LOCATION_HELP_TEXT,
      ),
      configStoreSettingsId=setting_id_config,
  )


def GetSettingResourceSpec(with_setting_id=True):
  fallthroughs = None
  if not with_setting_id:
    fallthroughs = [
        deps.ValueFallthrough(_UNUSED_SETTING_ID, hint='it is not required')
    ]
  setting_id_config = concepts.ResourceParameterAttributeConfig(
      name='setting_id',
      help_text=_SETTING_ID_HELP_TEXT,
      fallthroughs=fallthroughs,
  )
  return multitype.MultitypeResourceSpec(
      'setting',
      _ProjectSettingResourceSpec(setting_id_config),
      _FolderSettingResourceSpec(setting_id_config),
      _OrgSettingResourceSpec(setting_id_config),
  )


def AddConfigStoreSettingResourceArg(parser, verb, with_setting_id=True):
  """Adds the multitype ConfigStore setting resource arg to the parser.

  Args:
    parser: the argparse parser to add the resource arg to.
    verb: str, the verb phrase describing what happens to the setting(s), e.g.
      'to delete'.
    with_setting_id: bool, False for commands `list`. The SETTING positional is
      then omitted and only the attributes `--location`, `--folder`,
      `--organization`, `--project` are exposed.
  """
  concept_parsers.ConceptParser([
      presentation_specs.MultitypeResourcePresentationSpec(
          'setting',
          GetSettingResourceSpec(with_setting_id),
          f'The ConfigStore setting {verb}.',
          required=True,
          flag_name_overrides=(None if with_setting_id else {'setting_id': ''}),
      )
  ]).AddToParser(parser)


def GetParentRelativeName(setting_ref):
  """Returns the parent relative name for a ConfigStore setting resource."""
  # Parent() auto-resolves for folder and organization settings, but not for
  # project settings: the dataflow projects.locations collection uses the legacy
  # parameter names (projectId/location), which do not match the setting's
  # projectsId/locationsId parameters, so the parent cannot be resolved.
  if setting_ref.Collection() == _PROJECT_SETTING_COLLECTION:
    return (
        f'projects/{setting_ref.projectsId}/locations/{setting_ref.locationsId}'
    )
  return setting_ref.Parent().RelativeName()
