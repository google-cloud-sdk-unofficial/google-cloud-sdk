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
"""Command to Sync local workspace to a Cloud Run Service."""

import argparse

from googlecloudsdk.api_lib.run import service
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

_MIN_INSTANCES_ANNOTATION = 'autoscaling.knative.dev/minScale'
_MAX_INSTANCES_ANNOTATION = 'autoscaling.knative.dev/maxScale'


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


def NecessaryChangesForServicesDevSync(
    args: argparse.Namespace,
) -> list[config_changes.ConfigChanger]:
  """Adds necessary changes for service used by dev sync, if not specified by flags.

  1. Set SSH Enabled for the new Service
  2. Set Execution Environment to gen2
  3. Set min and max number of instances to 1

  Args:
    args: The command-line arguments.

  Returns:
    A list of Config Changes objects to apply to the Service for Dev Sync.
  """
  changes = [
      config_changes.SetAnnotationChange(
          'run.googleapis.com/ssh-enabled', 'true'
      ),
  ]
  if getattr(args, 'execution_environment', None) is None:
    changes.append(config_changes.SandboxChange(sandbox='gen2'))

  if getattr(args, 'min', None) is None:
    changes.append(
        config_changes.SetTemplateAnnotationChange(
            _MIN_INSTANCES_ANNOTATION, '1'
        )
    )
  if getattr(args, 'max', None) is None:
    changes.append(
        config_changes.SetTemplateAnnotationChange(
            _MAX_INSTANCES_ANNOTATION, '1'
        )
    )

  return changes


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.Hidden
class Sync(base.Command):
  """A command to sync local workspace to a Cloud Run Service."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Syncs the local workspace to Cloud Run Service.
          """
      ),
      'EXAMPLES': (
          """\
          To sync the local workspace to a Cloud Run Service:

              $ {command} my-service --source=.
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
    service_presentation = presentation_specs.ResourcePresentationSpec(
        'SERVICE',
        resource_args.GetServiceResourceSpec(prompt=True),
        'Service to sync to.',
        required=True,
        prefixes=False,
    )
    flags.AddServiceAccountFlag(parser)
    flags.AddIngressFlag(parser)
    flags.AddInvokerIamCheckFlag(parser)
    concept_parsers.ConceptParser([service_presentation]).AddToParser(parser)

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)
    container_args = ContainerArgGroup(cls.ReleaseTrack())
    container_parser.AddContainerFlags(
        parser, container_args, cls.ReleaseTrack()
    )

  def _CleanupService(self, args, service_ref):
    pretty_print.Info('Waiting for service to be deleted...')
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    with serverless_operations.Connect(conn_context) as client:
      deletion.Delete(
          service_ref, client.GetService, client.DeleteService, False
      )
      log.DeletedResource(service_ref.servicesId, 'service')

  def _ValidateServiceForDevSync(self, svc: service.Service):
    """Validates that the service is valid for dev sync."""
    min_scale = svc.annotations.get(_MIN_INSTANCES_ANNOTATION)
    max_scale = svc.annotations.get(_MAX_INSTANCES_ANNOTATION)

    if max_scale != '1' or min_scale != '1':
      pretty_print.Info(
          '{bold}**[Warning]**{reset} Service is not restricted to single'
          ' instance. Dev Sync will only update one instance. Set min & max'
          ' instances to 1 to avoid routing traffic to un-synced instances.'
      )

  def _GetService(self, args, service_ref) -> service.Service:
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )
    with serverless_operations.Connect(conn_context) as client:
      return client.GetService(service_ref)

  def Run(self, args):
    service_ref = args.CONCEPTS.service.Parse()
    flags.ValidateResource(service_ref)
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

    args.deployment_name = service_ref.Name()
    svc = self._GetService(args, service_ref)
    service_exists = svc is not None

    if service_exists:
      if args.cleanup:
        raise exceptions.ArgumentError(
            'The --cleanup flag is not supported for dev sync to an existing'
            ' Service.'
        )
      self._ValidateServiceForDevSync(svc)
    else:
      changes = NecessaryChangesForServicesDevSync(args)
      deploy_util.DeployServiceFromSource(
          service_ref=service_ref,
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
            workload_type=run_ssh.Ssh.WorkloadType.SERVICE,
            source=args.source,
        ).Run()
    except KeyboardInterrupt:
      pretty_print.Info(
          'Received Keyboard Interrupt... Dev Sync Session terminated'
      )
    finally:
      if args.cleanup and not service_exists:
        self._CleanupService(args, service_ref)
