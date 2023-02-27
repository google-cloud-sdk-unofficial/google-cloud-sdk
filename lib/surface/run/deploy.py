# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Deploy a container to Cloud Run."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import enum
import os.path

from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import traffic
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.artifacts import docker_util
from googlecloudsdk.command_lib.run import artifact_registry
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import messages_util
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import resource_change_validators
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker


def GetAllowUnauth(args, operations, service_ref, service_exists):
  """Returns allow_unauth value for a service change.

  Args:
    args: argparse.Namespace, Command line arguments
    operations: serverless_operations.ServerlessOperations, Serverless client.
    service_ref: protorpc.messages.Message, A resource reference object for the
      service See googlecloudsdk.core.resources.Registry.ParseResourceId for
      details.
    service_exists: True if the service being changed already exists.

  Returns:
    allow_unauth value where
     True means to enable unauthenticated acess for the service.
     False means to disable unauthenticated access for the service.
     None means to retain the current value for the service.
  """
  allow_unauth = None
  if platforms.GetPlatform() == platforms.PLATFORM_MANAGED:
    allow_unauth = flags.GetAllowUnauthenticated(args, operations, service_ref,
                                                 not service_exists)
    # Avoid failure removing a policy binding for a service that
    # doesn't exist.
    if not service_exists and not allow_unauth:
      allow_unauth = None
  return allow_unauth


class BuildType(enum.Enum):
  DOCKERFILE = 'Dockerfile'
  BUILDPACKS = 'Buildpacks'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Deploy(base.Command):
  """Create or update a Cloud Run service."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Creates or updates a Cloud Run service.
          """,
      'EXAMPLES':
          """\
          To deploy a container to the service `my-backend` on Cloud Run:

              $ {command} my-backend --image=us-docker.pkg.dev/project/image

          You may also omit the service name. Then a prompt will be displayed
          with a suggested default value:

              $ {command} --image=us-docker.pkg.dev/project/image

          To deploy to Cloud Run on Kubernetes Engine, you need to specify a cluster:

              $ {command} --image=us-docker.pkg.dev/project/image --cluster=my-cluster
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    # Flags specific to managed CR
    managed_group = flags.GetManagedArgGroup(parser)
    flags.AddAllowUnauthenticatedFlag(managed_group)
    flags.AddBinAuthzPolicyFlags(managed_group)
    flags.AddBinAuthzBreakglassFlag(managed_group)
    flags.AddCloudSQLFlags(managed_group)
    flags.AddCpuThrottlingFlag(managed_group)
    flags.AddRevisionSuffixArg(managed_group)
    flags.AddSandboxArg(managed_group)
    flags.AddVpcConnectorArgs(managed_group)
    flags.AddEgressSettingsFlag(managed_group)
    flags.AddCmekKeyFlag(managed_group)
    flags.AddCmekKeyRevocationActionTypeFlag(managed_group)
    flags.AddDescriptionFlag(managed_group)

    # Flags specific to connecting to a cluster
    cluster_group = flags.GetClusterArgGroup(parser)
    flags.AddEndpointVisibilityEnum(cluster_group)
    flags.AddConfigMapsFlags(cluster_group)

    # Flags not specific to any platform
    service_presentation = presentation_specs.ResourcePresentationSpec(
        'SERVICE',
        resource_args.GetServiceResourceSpec(prompt=True),
        'Service to deploy to.',
        required=True,
        prefixes=False)
    flags.AddPlatformAndLocationFlags(parser)
    flags.AddFunctionArg(parser)
    flags.AddMutexEnvVarsFlags(parser)
    flags.AddMemoryFlag(parser)
    flags.AddConcurrencyFlag(parser)
    flags.AddTimeoutFlag(parser)
    flags.AddAsyncFlag(parser)
    flags.AddLabelsFlags(parser)
    flags.AddGeneralAnnotationFlags(parser)
    flags.AddMinInstancesFlag(parser)
    flags.AddMaxInstancesFlag(parser)
    flags.AddCommandFlag(parser)
    flags.AddArgsFlag(parser)
    flags.AddPortFlag(parser)
    flags.AddCpuFlag(parser)
    flags.AddNoTrafficFlag(parser)
    flags.AddDeployTagFlag(parser)
    flags.AddServiceAccountFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    flags.AddIngressFlag(parser)
    flags.AddHttp2Flag(parser)
    flags.AddSourceAndImageFlags(parser)
    flags.AddSecretsFlags(parser)
    concept_parsers.ConceptParser([service_presentation]).AddToParser(parser)
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  @staticmethod
  def Args(parser):
    Deploy.CommonArgs(parser)

  def Run(self, args):
    """Deploy a container to Cloud Run."""
    platform = flags.GetAndValidatePlatform(
        args, self.ReleaseTrack(), flags.Product.RUN)

    include_build = flags.FlagIsExplicitlySet(args, 'source')
    if not include_build and not args.IsSpecified('image'):
      if console_io.CanPrompt():
        args.source = flags.PromptForDefaultSource()
        include_build = True
      else:
        raise c_exceptions.RequiredArgumentException(
            '--image', 'Requires a container image to deploy (e.g. '
            '`gcr.io/cloudrun/hello:latest`) if no build source is provided.')

    service_ref = args.CONCEPTS.service.Parse()
    flags.ValidateResource(service_ref)

    # Obtaining the connection context prompts the user to select a region if
    # one hasn't been provided. We want to do this prior to preparing a source
    # deploy so that we can use that region for the Artifact Registry repo.
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack())

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
          location_id=artifact_registry.RepoRegion(
              args,
              cluster_location=(conn_context.cluster_location if
                                platform == platforms.PLATFORM_GKE else None)),
          repo_id='cloud-run-source-deploy')
      if artifact_registry.ShouldCreateRepository(ar_repo):
        repo_to_create = ar_repo
      # The image is built with latest tag. After build, the image digest
      # from the build result will be added to the image of the service spec.
      args.image = '{repo}/{service}'.format(
          repo=ar_repo.GetDockerString(),
          service=service_ref.servicesId)
      # Use GCP Buildpacks if Dockerfile doesn't exist
      docker_file = source + '/Dockerfile'
      if os.path.exists(docker_file):
        build_type = BuildType.DOCKERFILE
      else:
        pack = [{'image': args.image}]
        if self.ReleaseTrack() is base.ReleaseTrack.ALPHA:
          command_arg = getattr(args, 'command', None)
          if command_arg is not None:
            command = ' '.join(command_arg)
            pack[0].update({
                'env': 'GOOGLE_ENTRYPOINT="{command}"'.format(command=command)
            })
        build_type = BuildType.BUILDPACKS
      image = None if pack else args.image
      operation_message = ('Building using {build_type} and deploying container'
                           ' to').format(build_type=build_type.value)
      pretty_print.Info(messages_util.GetBuildEquivalentForSourceRunMessage(
          service_ref.servicesId, pack, source))

    # Deploy a container with an image
    changes = flags.GetServiceConfigurationChanges(args)
    changes.insert(
        0,
        config_changes.DeleteAnnotationChange(
            k8s_object.BINAUTHZ_BREAKGLASS_ANNOTATION))
    changes.append(
        config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack()))

    with serverless_operations.Connect(conn_context) as operations:
      service = operations.GetService(service_ref)
      allow_unauth = GetAllowUnauth(args, operations, service_ref, service)
      resource_change_validators.ValidateClearVpcConnector(service, args)

      pretty_print.Info(
          messages_util.GetStartDeployMessage(conn_context, service_ref,
                                              operation_message))
      has_latest = (
          service is None or
          traffic.LATEST_REVISION_KEY in service.spec_traffic)
      deployment_stages = stages.ServiceStages(
          include_iam_policy_set=allow_unauth is not None,
          include_route=has_latest,
          include_build=include_build,
          include_create_repo=repo_to_create is not None,
      )
      header = None
      if include_build:
        header = 'Building and deploying'
      else:
        header = 'Deploying'
      if service is None:
        header += ' new service'
      header += '...'
      with progress_tracker.StagedProgressTracker(
          header,
          deployment_stages,
          failure_message='Deployment failed',
          suppress_output=args.async_) as tracker:
        service = operations.ReleaseService(
            service_ref,
            changes,
            tracker,
            asyn=args.async_,
            allow_unauthenticated=allow_unauth,
            prefetch=service,
            build_image=image,
            build_pack=pack,
            build_source=source,
            repo_to_create=repo_to_create)

      if args.async_:
        pretty_print.Success('Service [{{bold}}{serv}{{reset}}] is deploying '
                             'asynchronously.'.format(serv=service.name))
      else:
        service = operations.GetService(service_ref)
        pretty_print.Success(
            messages_util.GetSuccessMessageForSynchronousDeploy(service))
      return service


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaDeploy(Deploy):
  """Create or update a Cloud Run service."""

  @staticmethod
  def Args(parser):
    Deploy.CommonArgs(parser)

    # Flags specific to managed CR
    managed_group = flags.GetManagedArgGroup(parser)
    flags.AddSessionAffinityFlag(managed_group)
    flags.AddStartupCpuBoostFlag(managed_group)
    flags.AddEncryptionKeyShutdownHoursFlag(managed_group)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaDeploy(Deploy):
  """Create or update a Cloud Run service."""

  @staticmethod
  def Args(parser):
    Deploy.CommonArgs(parser)

    # Flags specific to managed CR
    managed_group = flags.GetManagedArgGroup(parser)
    flags.AddCustomAudiencesFlag(managed_group)
    flags.AddSessionAffinityFlag(managed_group)
    flags.AddStartupCpuBoostFlag(managed_group)
    flags.AddEncryptionKeyShutdownHoursFlag(managed_group)
    flags.AddVpcNetworkFlags(managed_group)
    flags.AddVpcSubnetFlags(managed_group)
    flags.AddVpcNetworkTagsFlags(managed_group)
    flags.AddRuntimeFlag(managed_group)

AlphaDeploy.__doc__ = Deploy.__doc__
