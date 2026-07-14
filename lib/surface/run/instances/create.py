# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Create a Cloud Run instance."""

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
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.generated_clients.apis.run.v1 import run_v1_messages as messages


EXAMPLE_INSTANCE_IMAGE = 'us-docker.pkg.dev/cloudrun/container/hello:latest'


def ContainerArgGroup(release_track=base.ReleaseTrack.ALPHA):
  """Returns an argument group with all per-container deploy args."""

  help_text = """
Container Flags

  If the --container is specified the following arguments may only be specified after a --container flag.
"""
  group = base.ArgumentGroup(help=help_text)
  # Verify image flag is specified in Run function for better error message.
  group.AddArgument(
      flags.ImageArg(image=EXAMPLE_INSTANCE_IMAGE, required=False)
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

  return group


def _GetAvailableRegions(
    e: exceptions.HttpError | api_util_exceptions.HttpException,
) -> list[str]:
  """Extracts available regions from a REGION_CAPACITY_EXHAUSTED error.

  Args:
    e: The exception to check.

  Returns:
    A list of available region names, or empty list if not applicable.
  """
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
class Create(base.Command):
  """Create a Cloud Run instance."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Creates a new Cloud Run instance.
          """
      ),
      'EXAMPLES': (
          """\
          To create a new instance `my-instance` on Cloud Run:

              $ {command} my-instance --image=us-docker.pkg.dev/project/image

          You may also omit the instance name. Then a prompt will be displayed
          with a suggested default value:

              $ {command} --image=us-docker.pkg.dev/project/image
          """
      ),
  }

  @classmethod
  def CommonArgs(cls, parser):
    # Flags not specific to any platform
    instance_presentation = presentation_specs.ResourcePresentationSpec(
        'INSTANCE',
        resource_args.GetInstanceResourceSpec(),
        'Instance to create.',
        required=False,
        prefixes=False,
    )
    flags.AddLabelsFlag(parser)
    flags.AddServiceAccountFlag(parser)
    flags.AddSetCloudSQLFlag(parser)
    flags.AddVpcNetworkGroupFlagsForCreate(parser, resource_kind='instance')
    flags.AddEgressSettingsFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    flags.AddBinAuthzPolicyFlags(parser, with_clear=False)
    flags.AddBinAuthzBreakglassFlag(parser)
    flags.AddCmekKeyFlag(parser, with_clear=False)
    flags.AddGeneralAnnotationFlags(parser)
    flags.AddVolumesFlags(parser, cls.ReleaseTrack())
    flags.AddIngressFlag(parser)
    flags.AddInvokerIamCheckFlag(parser)
    flags.AddRestartPolicyFlag(parser)
    flags.AddSshFlag(parser)
    flags.AddDefaultUrlFlag(parser, resource_kind='instance')

    polling_group = parser.add_mutually_exclusive_group()
    flags.AddAsyncFlag(polling_group)

    concept_parsers.ConceptParser([instance_presentation]).AddToParser(parser)
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  @staticmethod
  def Args(parser):
    Create.CommonArgs(parser)
    container_args = ContainerArgGroup()
    container_parser.AddContainerFlags(parser, container_args)

  def Run(self, args):
    """Deploy an Instance to Cloud Run."""
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
    elif not flags.FlagIsExplicitlySet(args, 'image'):
      raise c_parser_errors.RequiredError(argument='--image')

    instance_ref = args.CONCEPTS.instance.Parse()

    requested_instance_name = None
    if instance_ref:
      flags.ValidateResource(instance_ref)
      parent_ref = instance_ref.Parent()
      requested_instance_name = instance_ref.Name()
    else:
      # instance_ref is None, name not provided. Build parent_ref manually.
      project = properties.VALUES.core.project.Get(required=True)

      # Construct the parent reference (namespace)
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

    try:
      return self._DoCreate(
          conn_context,
          changes,
          parent_ref,
          requested_instance_name,
          args.async_,
      )
    except (exceptions.HttpError, api_util_exceptions.HttpException) as e:
      available_regions = _GetAvailableRegions(e)
      if not available_regions or args.quiet:
        raise e

      current_region = (
          getattr(conn_context, 'region', None)
          or properties.VALUES.run.region.Get()
      )
      return self._PromptAndRetry(
          e,
          available_regions,
          args,
          current_region,
          parent_ref,
          requested_instance_name,
      )

  def _DoCreate(
      self,
      conn_context: connection_context.ConnectionInfo,
      changes: Sequence[config_changes.ConfigChanger],
      parent_ref: resources.Resource,
      requested_instance_name: str | None,
      async_: bool,
  ) -> messages.Instance:
    """Execute the call to create a Cloud Run instance.

    Args:
      conn_context: The connection context for the API call.
      changes: A list of configuration changes to apply to the instance.
      parent_ref: The parent reference (namespace).
      requested_instance_name: The name of the instance.
      async_: whether to run asynchronously.

    Returns:
      The created instance object.

    Raises:
      exceptions.HttpError: If an HTTP error occurs during the API call.
    """
    with serverless_operations.Connect(conn_context) as operations:
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
        release_track = self.ReleaseTrack()
        release_track_prefix = (
            f' {release_track.prefix}'
            if release_track.prefix is not None
            else ''
        )
        log.status.Print(
            f'\nSee logs with:\ngcloud{release_track_prefix} run instances'
            f' logs tail {instance.name} --region {region}'
        )
        log.status.Print(
            f'\nSSH with:\ngcloud{release_track_prefix} run instances ssh'
            f' {instance.name} --region {region}'
        )
        if instance.urls:
          log.status.Print(f'\nURL: {instance.urls[0]}')
      return instance

  def _PromptAndRetry(
      self,
      e: exceptions.HttpError | api_util_exceptions.HttpException,
      available_regions: list[str],
      args: argparse.Namespace,
      current_region: str | None,
      parent_ref: resources.Resource,
      requested_instance_name: str | None,
  ) -> messages.Instance:
    """Prompts the user to select a region and retries creation.

    Args:
      e: The original exception to raise if user cancels.
      available_regions: List of available regions to choose from.
      args: The command arguments.
      current_region: The region that was exhausted.
      parent_ref: The parent reference (namespace).
      requested_instance_name: The name of the instance.

    Returns:
      The created instance.

    Raises:
      OperationCancelledError: If the user cancels.
      HttpError: If the retry fails.
    """
    idx = console_io.PromptChoice(
        available_regions,
        message=(
            f'Capacity exhausted in {current_region}. '
            'Would you like to select a different region?\n'
        ),
        cancel_option=True,
    )
    if idx is not None:
      args.region = available_regions[idx]
      conn_context = connection_context.GetConnectionContext(
          args, flags.Product.RUN, self.ReleaseTrack()
      )
      changes = flags.GetInstanceConfigurationChanges(
          args, release_track=self.ReleaseTrack()
      )
      changes.append(
          config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack())
      )
      return self._DoCreate(
          conn_context,
          changes,
          parent_ref,
          requested_instance_name,
          args.async_,
      )
    raise e
