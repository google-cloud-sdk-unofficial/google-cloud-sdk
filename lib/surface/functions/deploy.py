# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Creates or updates a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions import secrets_config
from googlecloudsdk.command_lib.functions.v1.deploy import command as command_v1
from googlecloudsdk.command_lib.functions.v1.deploy import labels_util
from googlecloudsdk.command_lib.functions.v2.deploy import command as command_v2
from googlecloudsdk.command_lib.functions.v2.deploy import env_vars_util
from googlecloudsdk.command_lib.util.args import labels_util as args_labels_util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Deploy(base.Command):
  """Create or update a Google Cloud Function."""

  @staticmethod
  def Args(parser, track=base.ReleaseTrack.GA):
    """Register base flags for this command."""
    # Add a positional "resource argument" for the name of the function
    flags.AddFunctionResourceArg(parser, 'to deploy')

    # Add `args.memory` as str. Converted at runtime to int for v1.
    flags.AddFunctionMemoryFlag(parser, track)

    # Add args for function properties
    flags.AddAllowUnauthenticatedFlag(parser)
    flags.AddFunctionRetryFlag(parser)
    flags.AddFunctionTimeoutFlag(parser, track)
    flags.AddMaxInstancesFlag(parser)
    flags.AddMinInstancesFlag(parser)
    flags.AddRuntimeFlag(parser)
    flags.AddServiceAccountFlag(parser)
    args_labels_util.AddUpdateLabelsFlags(
        parser,
        extra_update_message=labels_util.NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE,
        extra_remove_message=labels_util.NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE)

    # Add args for specifying the function source code
    flags.AddSourceFlag(parser)
    flags.AddStageBucketFlag(parser)
    flags.AddEntryPointFlag(parser)

    # Add args for specifying the function trigger
    flags.AddTriggerFlagGroup(parser, track)

    # Add args for specifying environment variables
    env_vars_util.AddUpdateEnvVarsFlags(parser)

    # Add flags for specifying build environment variables
    env_vars_util.AddBuildEnvVarsFlags(parser)

    # Add args for specifying ignore files to upload source
    flags.AddIgnoreFileFlag(parser)

    # Add flags for CMEK
    flags.AddKMSKeyFlags(parser)
    flags.AddDockerRepositoryFlags(parser)

    # Add flags for secrets
    secrets_config.ConfigureFlags(parser)

    # Add flags for network settings
    flags.AddVPCConnectorMutexGroup(parser)
    flags.AddEgressSettingsFlag(parser)
    flags.AddIngressSettingsFlag(parser)
    flags.AddSecurityLevelFlag(parser)
    flags.AddBuildWorkerPoolMutexGroup(parser)

  def Run(self, args):
    # For v1 convert args.memory from str to number of bytes in int
    args.memory = flags.ParseMemoryStrToNumBytes(args.memory)
    return command_v1.Run(args, track=self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeployBeta(Deploy):
  """Create or update a Google Cloud Function."""

  @staticmethod
  def Args(parser, track=base.ReleaseTrack.BETA):
    """Register beta flags for this command."""
    Deploy.Args(parser, track)

    # Configure flags for Artifact Registry
    flags.AddDockerRegistryFlags(parser)

    # Add additional flags for GCFv2
    flags.AddRunServiceAccountFlag(parser, track)
    flags.AddTriggerLocationFlag(parser, track)
    flags.AddTriggerServiceAccountFlag(parser, track)
    flags.AddGen2Flag(parser, track)
    flags.AddServeAllTrafficLatestRevisionFlag(parser)

  def Run(self, args):
    if flags.ShouldUseGen2():
      return command_v2.Run(args, self.ReleaseTrack())
    else:
      # For v1 convert args.memory from str to number of bytes in int
      args.memory = flags.ParseMemoryStrToNumBytes(args.memory)
      return command_v1.Run(args, track=self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeployAlpha(DeployBeta):
  """Create or update a Google Cloud Function."""

  @staticmethod
  def Args(parser, track=base.ReleaseTrack.ALPHA):
    """Register alpha (and implicitly beta) flags for this command."""
    DeployBeta.Args(parser, track)

  def Run(self, args):
    if flags.ShouldUseGen2():
      return command_v2.Run(args, self.ReleaseTrack())
    else:
      # Convert args.memory from str to number of bytes in int
      args.memory = flags.ParseMemoryStrToNumBytes(args.memory)
      return command_v1.Run(args, track=self.ReleaseTrack())


DETAILED_HELP = {
    'EXAMPLES':
        """\
        To deploy a function that is triggered by write events on the document
        ``/messages/{pushId}'', run:

          $ {command} my_function --runtime=python37 --trigger-event=providers/cloud.firestore/eventTypes/document.write --trigger-resource=projects/project_id/databases/(default)/documents/messages/{pushId}

        See https://cloud.google.com/functions/docs/calling for more details
        of using other types of resource as triggers.
        """
}

Deploy.detailed_help = DETAILED_HELP
DeployBeta.detailed_help = DETAILED_HELP
DeployAlpha.detailed_help = DETAILED_HELP
