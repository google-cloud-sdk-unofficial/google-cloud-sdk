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
"""Command for updating env vars and other configuration info."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def ContainerArgGroup():
  """Returns an argument group with all container update args."""

  help_text = """
Container Flags

  The following flags apply to the container.
"""
  group = base.ArgumentGroup(help=help_text)
  group.AddArgument(flags.ImageArg(required=False))
  group.AddArgument(flags.MutexEnvVarsFlags())
  group.AddArgument(flags.MemoryFlag())
  group.AddArgument(flags.CpuFlag())
  group.AddArgument(flags.CommandFlag())
  group.AddArgument(flags.ArgsFlag())
  group.AddArgument(flags.SecretsFlags())
  # ALPHA features
  group.AddArgument(flags.AddVolumeMountFlag())
  group.AddArgument(flags.RemoveVolumeMountFlag())
  group.AddArgument(flags.ClearVolumeMountsFlag())
  group.AddArgument(flags.GpuFlag())

  return group


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Update Cloud Run environment variables and other configuration settings."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To update one or more env vars:

              $ {command} myworkerpool --update-env-vars=KEY1=VALUE1,KEY2=VALUE2
         """,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddBinAuthzPolicyFlags(parser)
    flags.AddBinAuthzBreakglassFlag(parser)
    flags.AddCloudSQLFlags(parser)
    flags.AddCmekKeyFlag(parser)
    flags.AddCmekKeyRevocationActionTypeFlag(parser)
    flags.AddCustomAudiencesFlag(parser)
    flags.AddEgressSettingsFlag(parser)
    flags.AddEncryptionKeyShutdownHoursFlag(parser)
    flags.AddMinInstancesFlag(parser, resource_kind='worker')
    flags.AddMaxInstancesFlag(parser, resource_kind='worker')
    flags.AddMaxSurgeFlag(parser, resource_kind='worker')
    flags.AddMaxUnavailableFlag(parser, resource_kind='worker')
    flags.AddScalingFlag(parser)
    flags.AddRevisionSuffixArg(parser)
    flags.AddSessionAffinityFlag(parser)
    flags.AddVpcNetworkGroupFlagsForUpdate(parser, resource_kind='worker')
    flags.AddRuntimeFlag(parser)
    flags.AddDescriptionFlag(parser)
    flags.AddVolumesFlags(parser, cls.ReleaseTrack())
    flags.AddGpuTypeFlag(parser)
    flags.SERVICE_MESH_FLAG.AddToParser(parser)
    container_args = ContainerArgGroup()
    container_args.AddToParser(parser)
    flags.AddAsyncFlag(parser)
    flags.AddLabelsFlags(parser)
    flags.AddGeneralAnnotationFlags(parser)
    flags.AddServiceAccountFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    flags.AddNoPromoteFlag(parser)
    worker_pool_presentation = presentation_specs.ResourcePresentationSpec(
        'WORKER_POOL',
        resource_args.GetWorkerPoolResourceSpec(prompt=True),
        'WorkerPool to update the configuration of.',
        required=True,
        prefixes=False,
    )
    concept_parsers.ConceptParser([worker_pool_presentation]).AddToParser(
        parser
    )
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  def Run(self, args):
    """Update the worker-pool resource."""
    raise NotImplementedError
