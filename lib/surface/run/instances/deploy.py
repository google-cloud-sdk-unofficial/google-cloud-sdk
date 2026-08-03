# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Deploy a Cloud Run instance (create if not found, or update if exists)."""

import argparse
from collections.abc import Sequence
from googlecloudsdk.api_lib.util import exceptions as api_util_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.calliope import parser_errors as c_parser_errors
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import container_parser
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import messages_util
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.generated_clients.apis.run.v1 import run_v1_messages as messages

_EXAMPLE_INSTANCE_IMAGE = 'us-docker.pkg.dev/cloudrun/container/hello:latest'


def ContainerArgGroup(release_track=base.ReleaseTrack.ALPHA):
  """Returns an argument group with all per-container deploy args."""
  help_text = """\
  If the --container flag is specified, the following arguments may only be specified after a --container flag.
  """
  group = base.ArgumentGroup(help=help_text)
  group.AddArgument(
      flags.ImageArg(image=_EXAMPLE_INSTANCE_IMAGE, required=False)
  )
  group.AddArgument(flags.PortArg())
  group.AddArgument(flags.MutexEnvVarsFlags(release_track=release_track))
  group.AddArgument(flags.MemoryFlag())
  group.AddArgument(flags.CpuFlag())
  group.AddArgument(flags.ArgsFlag())
  group.AddArgument(flags.SecretsFlags())
  group.AddArgument(flags.CommandFlag())
  group.AddArgument(flags.DependsOnFlag())
  group.AddArgument(flags.AddVolumeMountFlag())
  group.AddArgument(flags.RemoveVolumeMountFlag())
  group.AddArgument(flags.ClearVolumeMountsFlag())
  group.AddArgument(flags.StartupProbeFlag())
  group.AddArgument(flags.SandboxLauncherFlag())
  return group


def _GetAvailableRegions(
    e: exceptions.HttpError | api_util_exceptions.HttpException,
) -> list[str]:
  """Extracts available regions from a REGION_CAPACITY_EXHAUSTED error."""
  if not isinstance(
      e, (exceptions.HttpError, api_util_exceptions.HttpException)
  ):
    return []

  # gcloud-disable-gdu-domain
  domain_details = e.payload.domain_details.get('run.googleapis.com', [])
  for detail in domain_details:
    if detail.get('reason') == 'REGION_CAPACITY_EXHAUSTED':
      metadata = detail.get('metadata', {})
      regions_str = metadata.get('available_regions', '')
      if regions_str:
        return regions_str.split(',')
      break
  return []


@base.UniverseCompatible
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Deploy(base.Command):
  """Deploy a Cloud Run instance."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Deploys a Cloud Run instance. If the instance does not exist yet, it is created.
          If the instance already exists, its container configuration is updated.
          """
      ),
      'EXAMPLES': (
          """\
          To deploy a new instance `my-instance` on Cloud Run:

              $ {command} my-instance --image=us-docker.pkg.dev/project/image

          To update an existing instance `my-instance` with a new container image:

              $ {command} my-instance --image=us-docker.pkg.dev/project/new-image
          """
      ),
  }

  @classmethod
  def CommonArgs(cls, parser):
    instance_presentation = presentation_specs.ResourcePresentationSpec(
        'INSTANCE',
        resource_args.GetInstanceResourceSpec(),
        'Instance to deploy.',
        required=False,
        prefixes=False,
    )
    flags.AddLabelsFlags(parser)
    flags.AddServiceAccountFlag(parser)
    flags.AddSetCloudSQLFlag(parser)
    flags.AddVpcNetworkGroupFlagsForUpdate(parser, resource_kind='instance')
    flags.AddEgressSettingsFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    flags.AddBinAuthzPolicyFlags(parser, with_clear=True)
    flags.AddBinAuthzBreakglassFlag(parser)
    flags.AddCmekKeyFlag(parser, with_clear=False)
    flags.AddGeneralAnnotationFlags(parser)
    flags.AddVolumesFlags(parser, cls.ReleaseTrack())
    flags.AddIngressFlag(parser)
    flags.AddInvokerIamCheckFlag(parser)
    flags.AddPublicFlag(parser)
    flags.AddRestartPolicyFlag(parser)
    flags.AddSshFlag(parser)
    flags.AddDefaultUrlFlag(parser, resource_kind='instance')

    polling_group = parser.add_mutually_exclusive_group()
    flags.AddAsyncFlag(polling_group)

    concept_parsers.ConceptParser([instance_presentation]).AddToParser(parser)
    parser.display_info.AddFormat('none')

  @staticmethod
  def Args(parser):
    Deploy.CommonArgs(parser)
    container_args = ContainerArgGroup()
    container_parser.AddContainerFlags(parser, container_args)
    flags.RemoveContainersFlag().AddToParser(parser)

  def Run(self, args: argparse.Namespace) -> messages.Instance:
    """Deploy an Instance to Cloud Run (Create if missing, Update if exists)."""
    flags.ValidatePublicFlags(args)
    if flags.FlagIsExplicitlySet(args, 'containers'):
      containers = args.containers
      if len(containers) > 10:
        raise c_exceptions.InvalidArgumentException(
            '--container', 'Instances may include at most 10 containers'
        )
      needs_image = {
          name: container
          for name, container in containers.items()
          if not container.IsSpecified('image')
      }
      if needs_image:
        raise exceptions.RequiredImageArgumentException(needs_image)

    instance_ref = args.CONCEPTS.instance.Parse()
    requested_instance_name = None
    if instance_ref:
      flags.ValidateResource(instance_ref)
      parent_ref = instance_ref.Parent()
      requested_instance_name = instance_ref.Name()
    else:
      project = properties.VALUES.core.project.Get(required=True)
      parent_ref = resources.REGISTRY.Create(
          'run.namespaces', namespacesId=project
      )

    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    changes = flags.GetInstanceConfigurationChanges(
        args, release_track=self.ReleaseTrack()
    )
    changes.append(
        config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack())
    )

    with serverless_operations.Connect(conn_context) as operations:
      existing_instance = None
      if instance_ref:
        existing_instance = operations.GetInstance(instance_ref)

      if existing_instance is None:
        if not flags.FlagIsExplicitlySet(
            args, 'image'
        ) and not flags.FlagIsExplicitlySet(args, 'containers'):
          raise c_parser_errors.RequiredError(argument='--image')
        return self._DoCreate(
            operations,
            conn_context,
            changes,
            parent_ref,
            requested_instance_name,
            args,
        )
      else:
        return self._DoUpdate(
            operations,
            conn_context,
            changes,
            instance_ref,
            existing_instance,
            args,
        )

  def _DoCreate(
      self,
      operations: serverless_operations.ServerlessOperations,
      conn_context: connection_context.ConnectionInfo,
      changes: Sequence[config_changes.ConfigChanger],
      parent_ref: resources.Resource,
      requested_instance_name: str | None,
      args: argparse.Namespace,
  ) -> messages.Instance:
    """Execute the call to create a Cloud Run instance."""
    async_ = args.async_
    pretty_print.Info(
        messages_util.GetStartCreateInstanceMessage(
            conn_context, parent_ref, requested_instance_name
        )
    )
    header_msg = 'Creating instance...'

    with progress_tracker.StagedProgressTracker(
        header_msg,
        stages.InstanceStages(),
        failure_message='Instance failed to deploy',
        suppress_output=async_,
    ) as tracker:
      instance = operations.CreateInstance(
          parent_ref,
          requested_instance_name,
          changes,
          tracker,
          asyn=async_,
      )
    if async_:
      pretty_print.Success(
          f'Instance [{{bold}}{instance.name}{{reset}}] is being created '
          'asynchronously.'
      )
    else:
      pretty_print.Success(
          f'Instance [{{bold}}{instance.name}{{reset}}] has successfully been'
          ' created.'
      )
      region = (
          getattr(conn_context, 'region', None)
          or properties.VALUES.run.region.Get()
      )
      messages_util.LogInstancePostDeploymentMessages(
          instance, region, self.ReleaseTrack()
      )
    return instance

  def _DoUpdate(
      self,
      operations: serverless_operations.ServerlessOperations,
      conn_context: connection_context.ConnectionInfo,
      changes: Sequence[config_changes.ConfigChanger],
      instance_ref: resources.Resource,
      existing_instance: messages.Instance,
      args: argparse.Namespace,
  ) -> messages.Instance:
    """Execute the call to update an existing Cloud Run instance."""
    pretty_print.Info(
        messages_util.GetStartDeployMessage(
            conn_context, instance_ref, 'Updating', 'instance'
        )
    )
    header_msg = 'Updating instance...'

    with progress_tracker.StagedProgressTracker(
        header_msg,
        stages.InstanceStages(),
        failure_message='Instance failed to deploy',
        suppress_output=args.async_,
    ) as tracker:
      instance = operations.UpdateInstance(
          instance_ref,
          existing_instance,
          changes,
          tracker,
          asyn=args.async_,
      )

    if args.async_:
      pretty_print.Success(
          f'Instance [{{bold}}{instance.name}{{reset}}] is being'
          ' updated asynchronously.'
      )
    else:
      pretty_print.Success(
          f'Instance [{{bold}}{instance.name}{{reset}}] has'
          ' successfully been updated.'
      )
      region = (
          getattr(conn_context, 'region', None)
          or properties.VALUES.run.region.Get()
      )
      messages_util.LogInstancePostDeploymentMessages(
          instance, region, self.ReleaseTrack()
      )
    return instance
