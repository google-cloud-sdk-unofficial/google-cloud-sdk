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
"""Command to Sync local workspace to a Cloud Run Instance."""

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import container_parser
from googlecloudsdk.command_lib.run import deletion
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run.sourcedeploys import deploy_util
from googlecloudsdk.command_lib.run.sync import sync_util
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


def ContainerArgGroup(release_track=base.ReleaseTrack.GA):
  """Returns an argument group with all container deploy args."""

  help_text = """
Container Flags

  The following flags apply to the container.
"""
  group = base.ArgumentGroup(help=help_text)
  group.AddArgument(flags.SourceArg())
  group.AddArgument(flags.PortArg())
  group.AddArgument(flags.MutexBuildEnvVarsFlags())
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
  group.AddArgument(flags.SandboxLauncherFlag(hidden=True))
  return group


def NecessaryChangesForInstancesDevSync(args):
  """Adds necessary changes for instances used by dev sync, if not specified by flags.

  1. Set SSH Enabled for the new Instance
  2. Set port to 8080

  Args:
    args: The command-line arguments.

  Returns:
    A list of Config Changes objects to apply to the Instances for Dev Sync.
  """
  changes = [
      # TODO(b/535075776): Add SSH Enabled annotation once the annotation is
      # available.
      # config_changes.SetAnnotationChange(
      #     service.SERVICE_SSH_ENABLED_ANNOTATION, 'true'
      # ),
  ]
  if getattr(args, 'port', None) is None:
    changes.append(config_changes.ContainerPortChange(port='8080'))

  return changes


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.Hidden
class Sync(base.Command):
  """Sync into a Cloud Run Instance."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Syncs the local workspace to Cloud Run Instance.
          """
      ),
      'EXAMPLES': (
          """\
          To sync the local workspace to a Cloud Run Instance:

              $ {command} my-instance --source=.
          """
      ),
  }

  @classmethod
  def CommonArgs(cls, parser):
    flags.DevSyncCleanupFlag(parser)
    parser.add_argument(
        '--iap-tunnel-url-override',
        hidden=True,
        help=(
            'Allows for overriding the connection endpoint for integration'
            ' testing.'
        ),
    )

    flags.CONFIG_MAP_FLAGS.AddToParser(parser)
    instance_presentation = presentation_specs.ResourcePresentationSpec(
        'INSTANCE',
        resource_args.GetInstanceResourceSpec(prompt=True),
        'Instance to sync to.',
        required=True,
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
    flags.AddPublicFlag(parser)
    flags.AddRestartPolicyFlag(parser)
    flags.AddDefaultUrlFlag(parser, resource_kind='instance')

    polling_group = parser.add_mutually_exclusive_group()
    flags.AddAsyncFlag(polling_group)

    concept_parsers.ConceptParser([instance_presentation]).AddToParser(parser)

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)
    container_args = ContainerArgGroup(cls.ReleaseTrack())
    container_parser.AddContainerFlags(
        parser, container_args, cls.ReleaseTrack()
    )

  def _Cleanup(self, args, instance_ref):
    pretty_print.Info('Waiting for instance to be deleted...')
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    with serverless_operations.Connect(conn_context) as client:
      deletion.Delete(
          instance_ref, client.GetInstance, client.DeleteInstance, False
      )
      log.DeletedResource(instance_ref.instancesId, 'instance')

  def _GetInstance(self, args, instance_ref):
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    with serverless_operations.Connect(conn_context) as client:
      return client.GetInstance(instance_ref)

  def Run(self, args):
    flags.ValidatePublicFlags(args)

    instance_ref = args.CONCEPTS.instance.Parse()
    flags.ValidateResource(instance_ref)
    args.release_track = self.ReleaseTrack()
    args.project = flags.GetProjectID(args)

    args.region = flags.GetRegion(args, prompt=False)
    if not args.region:
      raise exceptions.ArgumentError(
          'Missing required argument [region]. Set --region flag or set'
          ' run/region property.'
      )

    if not args.source:
      if console_io.CanPrompt():
        args.source = flags.PromptForDefaultSource()
      else:
        raise exceptions.ArgumentError(
            'The --source flag must be provided to specify the source for dev'
            ' sync.'
        )

    build_env_var_flags = map_util.GetMapFlagsFromArgs('build-env-vars', args)
    args.build_env_vars = (
        map_util.ApplyMapFlags(None, **build_env_var_flags) or {}
    )
    args.build_env_vars['GOOGLE_DEVSYNC'] = 'true'

    args.deployment_name = instance_ref.Name()
    instance = self._GetInstance(args, instance_ref)
    instance_exists = instance is not None

    if instance_exists:
      if args.cleanup:
        raise exceptions.ArgumentError(
            'The --cleanup flag is not supported for dev sync to an existing'
            ' Instance.'
        )
    else:
      changes = NecessaryChangesForInstancesDevSync(args)
      deploy_util.DeployInstanceFromSource(
          instance_ref=instance_ref,
          source=args.source,
          region=args.region,
          args=args,
          release_track=self.ReleaseTrack(),
          changes=changes,
      )

    try:
      with execution_utils.RaisesKeyboardInterrupt():
        sync_util.Sync(
            args=args,
            workload_type=run_ssh.Ssh.WorkloadType.INSTANCE,
            source=args.source,
        ).Run()
    except KeyboardInterrupt:
      pretty_print.Info(
          'Received Keyboard Interrupt... Dev Sync Session terminated'
      )
    finally:
      if args.cleanup and not instance_exists:
        self._Cleanup(args, instance_ref)
