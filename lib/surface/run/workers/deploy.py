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
import os.path
from googlecloudsdk.api_lib.run import api_enabler
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.run import artifact_registry
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import messages_util
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker


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


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Deploy(base.Command):
  """Create or update a Cloud Run worker."""

  detailed_help = {
      'DESCRIPTION': """\
          Creates or updates a Cloud Run worker.
          """,
      'EXAMPLES': """\
          To deploy a container to the worker `my-backend` on Cloud Run:

              $ {command} my-backend --image=us-docker.pkg.dev/project/image

          You may also omit the worker name. Then a prompt will be displayed
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
    worker_presentation = presentation_specs.ResourcePresentationSpec(
        'WORKER',
        resource_args.GetWorkerResourceSpec(prompt=True),
        'Worker to deploy to.',
        required=True,
        prefixes=False,
    )
    flags.AddAsyncFlag(parser)
    flags.AddLabelsFlags(parser)
    flags.AddGeneralAnnotationFlags(parser)
    flags.AddServiceAccountFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    flags.AddNoPromoteFlag(parser)
    concept_parsers.ConceptParser([worker_presentation]).AddToParser(parser)
    container_args = ContainerArgGroup()
    container_args.AddToParser(parser)

    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  def _GetTracker(
      self,
      args,
      worker,
      include_build,
      repo_to_create,
  ):
    deployment_stages = stages.WorkerStages(
        include_build=include_build,
        include_create_repo=repo_to_create is not None,
    )
    if include_build:
      header = 'Building and deploying'
    else:
      header = 'Deploying'
    if worker is None:
      header += ' new worker'
    header += '...'
    return progress_tracker.StagedProgressTracker(
        header,
        deployment_stages,
        failure_message='Deployment failed',
        suppress_output=args.async_,
    )

  def _GetBaseChanges(self, args, worker):
    """Returns the worker config changes with some default settings."""
    changes = flags.GetWorkerConfigurationChanges(
        args, self.ReleaseTrack(), for_update=worker is not None
    )
    changes.insert(
        0,
        config_changes.DeleteAnnotationChange(
            k8s_object.BINAUTHZ_BREAKGLASS_ANNOTATION
        ),
    )
    changes.append(
        config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack())
    )
    return changes

  def Run(self, args):
    """Deploy a Worker container to Cloud Run."""
    include_build = flags.FlagIsExplicitlySet(args, 'source')
    if not include_build and not args.IsSpecified('image'):
      if console_io.CanPrompt():
        args.source = flags.PromptForDefaultSource()
        include_build = True
      else:
        raise c_exceptions.RequiredArgumentException(
            '--image',
            'Requires a container image to deploy (e.g. '
            '`gcr.io/cloudrun/hello:latest`) if no build source is provided.',
        )

    worker_ref = args.CONCEPTS.worker.Parse()
    flags.ValidateResource(worker_ref)

    required_apis = [api_enabler.get_run_api()]
    # gcloud-disable-gdu-domain
    if include_build:
      required_apis.append('artifactregistry.googleapis.com')
      required_apis.append('cloudbuild.googleapis.com')

    already_activated_services = api_enabler.check_and_enable_apis(
        properties.VALUES.core.project.Get(), required_apis
    )
    # Obtaining the connection context prompts the user to select a region if
    # one hasn't been provided. We want to do this prior to preparing a source
    # deploy so that we can use that region for the Artifact Registry repo.
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )

    build_type = None
    image = None
    pack = None
    source = None
    operation_message = 'Deploying container to'
    repo_to_create = None
    # Build an image from source if source specified
    if include_build:
      source = args.source
      ar_repo = docker_util.DockerRepo(
          project_id=properties.VALUES.core.project.Get(required=True),
          location_id=artifact_registry.RepoRegion(args),
          repo_id='cloud-run-source-deploy',
      )
      if artifact_registry.ShouldCreateRepository(
          ar_repo, skip_activation_prompt=already_activated_services
      ):
        repo_to_create = ar_repo
      # The image is built with latest tag. After build, the image digest
      # from the build result will be added to the image of the service spec.
      args.image = '{repo}/{service}'.format(
          repo=ar_repo.GetDockerString(), service=worker_ref.servicesId
      )
      # Use GCP Buildpacks if Dockerfile doesn't exist
      docker_file = source + '/Dockerfile'
      if os.path.exists(docker_file):
        build_type = BuildType.DOCKERFILE
      else:
        pack = _CreateBuildPack(args, self.ReleaseTrack())
        build_type = BuildType.BUILDPACKS
      image = None if pack else args.image
      operation_message = (
          'Building using {build_type} and deploying container to'
      ).format(build_type=build_type.value)
      pretty_print.Info(
          messages_util.GetBuildEquivalentForSourceRunMessage(
              worker_ref.servicesId, pack, source
          )
      )

    with serverless_operations.Connect(
        conn_context, already_activated_services
    ) as operations:
      worker = operations.GetWorker(worker_ref)
      # Deploy a container with an image
      changes = self._GetBaseChanges(args, worker)
      pretty_print.Info(
          messages_util.GetStartDeployMessage(
              conn_context,
              worker_ref,
              operation_message,
              resource_kind_lower='worker',
          )
      )
      with self._GetTracker(
          args, worker, include_build, repo_to_create
      ) as tracker:
        worker = operations.ReleaseWorker(
            worker_ref,
            changes,
            self.ReleaseTrack(),
            tracker,
            asyn=args.async_,
            prefetch=worker,
            build_image=image,
            build_pack=pack,
            build_source=source,
            repo_to_create=repo_to_create,
            already_activated_services=already_activated_services,
            generate_name=flags.FlagIsExplicitlySet(args, 'revision_suffix'),
        )

      if args.async_:
        pretty_print.Success(
            'Worker [{{bold}}{serv}{{reset}}] is deploying '
            'asynchronously.'.format(serv=worker.name)
        )
      else:
        pretty_print.Success(
            messages_util.GetSuccessMessageForWorkerDeploy(
                worker, args.no_promote
            )
        )
      return worker


def _CreateBuildPack(args, release_track=base.ReleaseTrack.GA):
  """A helper method to cofigure buildpack."""
  pack = [{'image': args.image}]
  if release_track is base.ReleaseTrack.ALPHA:
    command_arg = getattr(args, 'command', None)
    if command_arg is not None:
      command = ' '.join(command_arg)
      pack[0].update(
          {'envs': ['GOOGLE_ENTRYPOINT="{command}"'.format(command=command)]}
      )
  return pack
