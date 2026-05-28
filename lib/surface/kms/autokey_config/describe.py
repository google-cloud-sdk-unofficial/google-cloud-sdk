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
"""Describe the AutokeyConfig of a folder or project."""

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags


@base.UniverseCompatible
class Describe(base.DescribeCommand):
  r"""Describe the AutokeyConfig of a folder or project.

  {command} can be used to retrieve the AutokeyConfig of a folder or project.

  ## EXAMPLES

  The following command retrieves the AutokeyConfig of a folder having folder-id
  `123`:

    $ {command} --folder=123

  The following command retrieves the AutokeyConfig of a project having
  project-id `my-project`:

    $ {command} --project=my-project
  """

  @staticmethod
  def Args(parser):
    flags.AddAutokeyConfigResourceFlags(parser)

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = client.MESSAGES_MODULE

    if args.folder:
      autokey_config_name = f'folders/{args.folder}/autokeyConfig'
      return client.folders.GetAutokeyConfig(
          messages.CloudkmsFoldersGetAutokeyConfigRequest(
              name=autokey_config_name
          )
      )

    # Otherwise, it is a project.
    autokey_config_name = f'projects/{args.project}/autokeyConfig'
    return client.projects.GetAutokeyConfig(
        messages.CloudkmsProjectsGetAutokeyConfigRequest(
            name=autokey_config_name
        )
    )
