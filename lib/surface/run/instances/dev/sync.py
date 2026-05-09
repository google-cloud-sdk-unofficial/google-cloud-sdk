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
  """Returns an argument group with all container deploy & sync args."""

  help_text = """
Container Flags

  The following flags apply to the container.
"""
  group = base.ArgumentGroup(help=help_text)
  group.AddArgument(
      flags.SourceAndImageFlags(
          mutex=False, no_build_enabled=True, release_track=release_track
      )
  )
  group.AddArgument(flags.PortArg())
  group.AddArgument(flags.MutexBuildEnvVarsFlags())
  return group


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
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
    flags.SkipDeployArg(parser)
    flags.KeepAliveAfterDevSyncFlag(parser)
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
    flags.AddServiceAccountFlag(parser)
    flags.AddIngressFlag(parser)
    flags.AddInvokerIamCheckFlag(parser)
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

  def Run(self, args):
    instance_ref = args.CONCEPTS.instance.Parse()
    args.project = flags.GetProjectID(args)
    args.region = flags.GetRegion(args, prompt=False)
    if not args.region:
      raise exceptions.ArgumentError(
          'Missing required argument [region]. Set --region flag or set'
          ' run/region property.'
      )
    args.release_track = self.ReleaseTrack()
    args.deployment_name = instance_ref.Name()
    build_env_var_flags = map_util.GetMapFlagsFromArgs('build-env-vars', args)
    args.build_env_vars = (
        map_util.ApplyMapFlags(None, **build_env_var_flags) or {}
    )
    args.build_env_vars['GOOGLE_DEVSYNC'] = 'true'

    if not args.source:
      if console_io.CanPrompt():
        args.source = flags.PromptForDefaultSource()
      else:
        raise exceptions.ArgumentError(
            'The --source flag must be provided to specify the source for dev'
            ' sync.'
        )

    if not args.skip_deploy:
      changes = sync_util.NecessaryChangesForInstancesDevSync(args)
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
      if not args.keep_alive_after_dev_sync and not args.skip_deploy:
        self._Cleanup(args, instance_ref)
