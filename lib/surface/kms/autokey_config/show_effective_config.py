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
"""Gets the effective Cloud KMS AutokeyConfig for a given project."""


from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import resource_args
from googlecloudsdk.core import properties


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class ShowEffectiveConfig(base.Command):
  r"""Gets the effective Cloud KMS AutokeyConfig for a given project.

  {command} can be used to get the effective Cloud KMS AutokeyConfig for a given
  project.

  ## EXAMPLES

  The following command retrieves the effective Cloud KMS AutokeyConfig for a
  given project `my-project`:

  $ {command} --project=my-project

  If --project flag is not provided, then the current project will be used.
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsProjectResourceArgForKMS(parser, True, 'project')

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    project_ref = args.CONCEPTS.project.Parse()

    return client.projects.ShowEffectiveAutokeyConfig(
        messages.CloudkmsProjectsShowEffectiveAutokeyConfigRequest(
            parent=project_ref.RelativeName()))


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ShowEffectiveConfigAlphaBeta(base.Command):
  r"""Get the effective Cloud KMS AutokeyConfig for a given folder or project.

  {command} can be used to get the effective Cloud KMS AutokeyConfig for a given
  folder or project.

  ## EXAMPLES

  The following command retrieves the effective Cloud KMS AutokeyConfig for a
  given folder `123`:

  $ {command} --folder=123

  The following command retrieves the effective Cloud KMS AutokeyConfig for a
  given project `my-project`:

  $ {command} --project=my-project

  If neither flag is provided, then the current project will be used.
  """

  @staticmethod
  def Args(parser):
    flags.AddAutokeyConfigResourceFlags(parser, required=False)

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    if args.folder:
      return client.folders.ShowEffectiveAutokeyConfig(
          messages.CloudkmsFoldersShowEffectiveAutokeyConfigRequest(
              parent=f'folders/{args.folder}'
          )
      )

    project = args.project or properties.VALUES.core.project.Get(required=True)
    return client.projects.ShowEffectiveAutokeyConfig(
        messages.CloudkmsProjectsShowEffectiveAutokeyConfigRequest(
            parent=f'projects/{project}'
        )
    )
