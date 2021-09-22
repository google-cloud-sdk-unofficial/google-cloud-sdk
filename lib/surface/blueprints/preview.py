# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Preview deployment command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.blueprints import blueprints_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.blueprints import deploy_util
from googlecloudsdk.command_lib.blueprints import flags
from googlecloudsdk.command_lib.blueprints import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.CreateCommand):
  """Preview deployment operations.

  This command previews update/delete operations on an existing deployment or
  create operation of a new deployment.
  """

  detailed_help = {
      'EXAMPLES': ("""
        Preview a new deployment from local files:

          $ gcloud alpha blueprints preview --source="./path/to/blueprint" \
              my-deployment-preview

        Preview an update to an existing deployment named my-deployment from
        local files and control which storage bucket the files are uploaded to:

          $ gcloud alpha blueprints preview --source="./path/to/blueprint" \
              --stage-bucket="gs://my-bucket" my-deployment

        Preview deletion of an exsting deployment named my-deployment:

          $ gcloud alpha blueprints preview my-deployment --delete

        Preview deletion of an exsting deployment named my-deployment and print
        verbose results in JSON format:

          $ gcloud alpha blueprints preview my-deployment --delete \
              --preview-format=json
      """)
  }

  @staticmethod
  def Args(parser):
    flags.AddPreviewFlags(parser)
    flags.AddPreviewFormatFlag(parser)
    flags.AddIgnoreFileFlag(parser)
    resource_args.AddDeploymentResourceArg(parser, 'the deployment to preview.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A messages.Preview resource.
    """
    messages = blueprints_util.GetMessagesModule()
    deployment_ref = args.CONCEPTS.deployment.Parse()
    deployment_full_name = deployment_ref.RelativeName()
    location = deployment_ref.Parent().Name()

    if args.delete:
      return deploy_util.PreviewDelete(deployment_full_name, messages, location,
                                       args.preview_format)
    else:
      return deploy_util.PreviewApply(args.source, deployment_full_name,
                                      args.stage_bucket, messages, location,
                                      args.ignore_file, args.source_git_subdir,
                                      args.preview_format)
