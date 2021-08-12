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
"""Create- and update-deployment command."""

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
  """Create or update a deployment.

  This command updates a deployment when it already exists, otherwise the
  deployment will be created.
  """

  detailed_help = {
      'EXAMPLES': ("""
        Create a deployment named ``my-deployment'' from local files:

          $ {command} --source="./path/to/blueprint" my-deployment

        Create a deployment named ``my-deployment'' from local files and control
        which storage bucket the files are uploaded to:

          $ {command} --source="./path/to/blueprint" --stage-bucket="gs://my-bucket" my-deployment

        Create a deployment named ``my-deployment'' from an existing storage
        bucket:

          $ {command} --source="gs://my-bucket" my-deployment

        Update a deployment's labels:

          $ {command} --source="https://github.com/google/repo@mainline" --labels="env=prod,team=finance" my-deployment
      """)
  }

  @staticmethod
  def Args(parser):
    flags.AddLabelsFlag(parser)
    flags.AddAsyncFlag(parser)
    flags.AddSourceFlag(parser)
    flags.AddIgnoreFileFlag(parser)
    flags.AddTimeoutFlag(parser)
    resource_args.AddDeploymentResourceArg(
        parser,
        'the deployment to create or update.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The resulting Deployment resource or, in the case that args.async_ is
        True, a long-running operation.
    """
    messages = blueprints_util.GetMessagesModule()
    deployment_ref = args.CONCEPTS.deployment.Parse()
    deployment_full_name = deployment_ref.RelativeName()
    location = deployment_ref.Parent().Name()

    return deploy_util.Apply(args.source, deployment_full_name,
                             args.stage_bucket, args.labels, messages, location,
                             args.ignore_file, args.async_,
                             args.reconcile_timeout, args.source_git_subdir)
