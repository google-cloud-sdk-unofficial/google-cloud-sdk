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
"""Update a Cloud Run instance."""

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import container_parser
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
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
from googlecloudsdk.core.console import progress_tracker


_EXAMPLE_INSTANCE_IMAGE = 'us-docker.pkg.dev/cloudrun/container/hello:latest'
_MAX_CONTAINERS_PER_INSTANCE = 10


def ContainerArgGroup(release_track=base.ReleaseTrack.ALPHA):
  """Returns an argument group with all per-container deploy args.

  Args:
    release_track: The release track of the command.
  """

  help_text = textwrap.dedent("""\
  Container Flags

      If the --container flag is specified, the following arguments may only
      be specified after a --container flag.""")
  group = base.ArgumentGroup(help=help_text)
  flags_to_add = [
      flags.ImageArg(image=_EXAMPLE_INSTANCE_IMAGE, required=False),
      flags.PortArg(),
      flags.MutexEnvVarsFlags(release_track=release_track),
      flags.MemoryFlag(),
      flags.CpuFlag(),
      flags.ArgsFlag(),
      flags.SecretsFlags(),
      flags.CommandFlag(),
      flags.DependsOnFlag(),
      flags.AddVolumeMountFlag(),
      flags.RemoveVolumeMountFlag(),
      flags.ClearVolumeMountsFlag(),
      flags.StartupProbeFlag(),
  ]
  for flag in flags_to_add:
    group.AddArgument(flag)
  return group


@base.UniverseCompatible
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaUpdate(base.Command):
  """Update a Cloud Run instance."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          Update one or more configuration settings of a Cloud Run instance
          (e.g. container image, environment variables, etc.). If the instance
          is running, it will be stopped and then recreated with the updated
          configurations.

          If the instance does not exist, this command will create one with the
          provided configuration settings.
          """),
      'EXAMPLES': textwrap.dedent("""\
          To update the container image of Cloud Run instance `my-instance`:

              $ {command} my-instance --image=us-docker.pkg.dev/project/image

          """),
  }

  @classmethod
  def CommonArgs(cls, parser):
    instance_presentation = presentation_specs.ResourcePresentationSpec(
        'INSTANCE',
        resource_args.GetInstanceResourceSpec(),
        'Instance to update.',
        required=True,
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
    flags.AddRestartPolicyFlag(parser)
    flags.AddSshFlag(parser)
    flags.AddDefaultUrlFlag(parser, resource_kind='instance')

    polling_group = parser.add_mutually_exclusive_group()
    flags.AddAsyncFlag(polling_group)

    concept_parsers.ConceptParser([instance_presentation]).AddToParser(parser)
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)
    container_args = ContainerArgGroup()
    container_parser.AddContainerFlags(parser, container_args)
    flags.RemoveContainersFlag().AddToParser(parser)

  def Run(self, args):
    """Update an Instance on Cloud Run."""
    if flags.FlagIsExplicitlySet(args, 'containers'):
      containers = args.containers
      if len(containers) > _MAX_CONTAINERS_PER_INSTANCE:
        raise exceptions.InvalidArgumentException(
            '--container', 'Instances may include at most 10 containers'
        )

    instance_ref = args.CONCEPTS.instance.Parse()
    flags.ValidateResource(instance_ref)

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
      existing_instance = operations.GetInstance(instance_ref)
      if existing_instance is None:
        raise serverless_exceptions.InstanceNotFoundError(
            f'Instance [{instance_ref.Name()}] not found.'
        )

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
        release_track = (
            f' {self.ReleaseTrack().prefix}'
            if self.ReleaseTrack().prefix
            else ''
        )
        log.status.Print(
            f'\nSee logs with:\ngcloud{release_track} run instances logs tail'
            f' {instance.name} --region {region}'
        )
        log.status.Print(
            f'\nSSH with:\ngcloud{release_track} run instances ssh'
            f' {instance.name} --region {region}'
        )
        if instance.urls:
          log.status.Print(f'\nURL: {instance.urls[0]}')

      return instance
