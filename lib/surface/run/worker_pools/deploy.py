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
"""Deploy a container to Cloud Run that will handle workloads that are not ingress based."""

import enum

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run.v2 import config_changes as config_changes_mod
from googlecloudsdk.command_lib.run.v2 import flags_parser
from googlecloudsdk.command_lib.run.v2 import worker_pools_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


class BuildType(enum.Enum):
  DOCKERFILE = 'Dockerfile'
  BUILDPACKS = 'Buildpacks'


def ContainerArgGroup():
  """Returns an argument group with all container deploy args."""

  help_text = """
Container Flags

  The following flags apply to the container.
"""
  group = base.ArgumentGroup(help=help_text)
  group.AddArgument(flags.SourceAndImageFlags())
  group.AddArgument(flags.MutexEnvVarsFlags())
  group.AddArgument(flags.MemoryFlag())
  group.AddArgument(flags.CpuFlag())
  group.AddArgument(flags.ArgsFlag())
  group.AddArgument(flags.SecretsFlags())
  group.AddArgument(flags.CommandFlag())
  # ALPHA features
  group.AddArgument(flags.AddVolumeMountFlag())
  group.AddArgument(flags.RemoveVolumeMountFlag())
  group.AddArgument(flags.ClearVolumeMountsFlag())
  group.AddArgument(flags.GpuFlag())

  return group


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Deploy(base.Command):
  """Create or update a Cloud Run worker-pool."""

  detailed_help = {
      'DESCRIPTION': """\
          Creates or updates a Cloud Run worker-pool.
          """,
      'EXAMPLES': """\
          To deploy a container to the worker-pool `my-backend` on Cloud Run:

              $ {command} my-backend --image=us-docker.pkg.dev/project/image

          You may also omit the worker-pool name. Then a prompt will be displayed
          with a suggested default value:

              $ {command} --image=us-docker.pkg.dev/project/image
          """,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddBinAuthzPolicyFlags(parser)
    flags.AddBinAuthzBreakglassFlag(parser)
    flags.AddCloudSQLFlags(parser)
    flags.AddCmekKeyFlag(parser)
    flags.AddCmekKeyRevocationActionTypeFlag(parser)
    flags.AddDescriptionFlag(parser)
    flags.AddEncryptionKeyShutdownHoursFlag(parser)
    flags.AddRevisionSuffixArg(parser)
    flags.AddRuntimeFlag(parser)
    flags.AddMinInstancesFlag(parser, resource_kind='worker')
    flags.AddMaxInstancesFlag(parser, resource_kind='worker')
    flags.AddMaxSurgeFlag(parser, resource_kind='worker')
    flags.AddMaxUnavailableFlag(parser, resource_kind='worker')
    flags.AddScalingFlag(parser)
    flags.AddVolumesFlags(parser, cls.ReleaseTrack())
    flags.AddGpuTypeFlag(parser)
    flags.AddVpcNetworkGroupFlagsForUpdate(parser, resource_kind='worker')
    flags.AddEgressSettingsFlag(parser)
    flags.SERVICE_MESH_FLAG.AddToParser(parser)
    flags.AddAsyncFlag(parser)
    flags.AddLabelsFlags(parser)
    flags.AddGeneralAnnotationFlags(parser)
    flags.AddServiceAccountFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    flags.AddNoPromoteFlag(parser)
    worker_pool_presentation = presentation_specs.ResourcePresentationSpec(
        'WORKER_POOL',
        resource_args.GetWorkerPoolResourceSpec(prompt=True),
        'WorkerPool to deploy to.',
        required=True,
        prefixes=False,
    )
    concept_parsers.ConceptParser([worker_pool_presentation]).AddToParser(
        parser
    )
    container_args = ContainerArgGroup()
    container_args.AddToParser(parser)

    # No output by default, can be overridden by --format
    # parser.display_info.AddFormat('none')

  def _GetBaseChanges(self, args):
    """Returns the worker pool config changes with some default settings."""
    changes = flags_parser.GetWorkerPoolConfigurationChanges(args)
    changes.insert(
        0,
        config_changes_mod.BinaryAuthorizationChange(
            breakglass_justification=None
        ),
    )
    changes.append(config_changes_mod.SetLaunchStageChange(self.ReleaseTrack()))
    return changes

  def Run(self, args):
    """Deploy a WorkerPool container to Cloud Run."""
    # TODO(b/366466235): Add support for source deploy.
    # TODO(b/376904673): Add progress tracker.
    if not args.IsSpecified('image'):
      raise c_exceptions.RequiredArgumentException(
          '--image',
          'Requires a container image to deploy (e.g. '
          '`gcr.io/cloudrun/hello:latest`).',
      )

    worker_pool_ref = args.CONCEPTS.worker_pool.Parse()
    flags.ValidateResource(worker_pool_ref)

    def DeriveRegionalEndpoint(endpoint):
      region = args.CONCEPTS.worker_pool.Parse().locationsId
      return region + '-' + endpoint

    run_client = apis.GetGapicClientInstance(
        'run', 'v2', address_override_func=DeriveRegionalEndpoint
    )
    worker_pools_client = worker_pools_operations.WorkerPoolsOperations(
        run_client
    )
    # pre-fetch the worker pool in case it already exists.
    worker_pool = worker_pools_client.GetWorkerPool(worker_pool_ref)
    config_changes = self._GetBaseChanges(args)
    response = worker_pools_client.ReleaseWorkerPool(
        worker_pool_ref, worker_pool, config_changes
    )
    if not response:
      raise exceptions.ArgumentError(
          'Cannot deploy WorkerPool [{}]'.format(worker_pool_ref.workerPoolsId)
      )
    # TODO(b/366576967): Support wait operation in sync mode.
    return response.operation
