# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Updates the AutokeyConfig for a folder or project."""

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import parsing


@base.UniverseCompatible
class Update(base.Command):
  r"""Update the AutokeyConfig for a folder or project.

  {command} can be used to update the AutokeyConfig for a folder or project.

  ## EXAMPLES

  The following command updates the AutokeyConfig for the folder or project
  mentioned in the config.yaml file:

    $ {command} config.yaml
  """

  @staticmethod
  def Args(parser):
    flags.AddAutokeyConfigFileFlag(parser)

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    name, key_project_resolution_mode, key_project, etag = (
        parsing.ReadAutokeyConfigFromConfigFileWithKeyProjectResolutionMode(
            args.CONFIG_FILE
        )
    )

    update_mask = []
    autokey_config = messages.AutokeyConfig(name=name)
    if key_project is not None:
      if key_project:
        autokey_config.keyProject = key_project
      update_mask.append("keyProject")
    if key_project_resolution_mode:
      autokey_config.keyProjectResolutionMode = (
          messages.AutokeyConfig.KeyProjectResolutionModeValueValuesEnum(
              key_project_resolution_mode
          )
      )
      update_mask.append("keyProjectResolutionMode")
    if etag:
      autokey_config.etag = etag

    if name.startswith("folders/"):
      return client.folders.UpdateAutokeyConfig(
          messages.CloudkmsFoldersUpdateAutokeyConfigRequest(
              autokeyConfig=autokey_config,
              name=name,
              updateMask=",".join(update_mask),
          ),
      )

    # Otherwise, it is a project.
    return client.projects.UpdateAutokeyConfig(
        messages.CloudkmsProjectsUpdateAutokeyConfigRequest(
            autokeyConfig=autokey_config,
            name=name,
            updateMask=",".join(update_mask),
        ),
    )
