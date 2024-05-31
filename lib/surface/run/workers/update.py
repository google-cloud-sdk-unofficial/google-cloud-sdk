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

from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import messages_util
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.console import progress_tracker


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

              $ {command} myworker --update-env-vars=KEY1=VALUE1,KEY2=VALUE2
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
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  def _ConnectionContext(self, args):
    return connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )

  def _GetBaseChanges(self, args):
    changes = flags.GetWorkerConfigurationChanges(
        args, self.ReleaseTrack(), for_update=True
    )
    if not changes or (
        len(changes) == 1
        and isinstance(
            changes[0], config_changes.SetClientNameAndVersionAnnotationChange
        )
    ):
      raise exceptions.NoConfigurationChangeError(
          'No configuration change requested. '
          'Did you mean to include the flags `--update-env-vars`, '
          '`--memory`, `--image`?'
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

  # TODO(b/322180968): Once Worker API is ready, replace Service related
  # references.
  def Run(self, args):
    """Update the worker resource.

       Different from `deploy` in that it can only update the worker spec but
       no IAM or Cloud build changes.

    Args:
      args: Args!

    Returns:
      googlecloudsdk.api_lib.run.Service, the updated service
    """
    changes = self._GetBaseChanges(args)

    conn_context = self._ConnectionContext(args)
    worker_ref = args.CONCEPTS.worker.Parse()
    flags.ValidateResource(worker_ref)

    with serverless_operations.Connect(conn_context) as client:
      worker = client.GetWorker(worker_ref)
      creates_revision = config_changes.AdjustsTemplate(changes)
      deployment_stages = stages.WorkerStages(
          include_create_revision=creates_revision,
      )
      if creates_revision:
        progress_message = 'Deploying...'
        failure_message = 'Deployment failed'
        result_message = 'deploying'
      else:
        progress_message = 'Updating...'
        failure_message = 'Update failed'
        result_message = 'updating'
      with progress_tracker.StagedProgressTracker(
          progress_message,
          deployment_stages,
          failure_message=failure_message,
          suppress_output=args.async_,
      ) as tracker:
        worker = client.ReleaseWorker(
            worker_ref,
            changes,
            self.ReleaseTrack(),
            tracker,
            asyn=args.async_,
            prefetch=worker,
            generate_name=(flags.FlagIsExplicitlySet(args, 'revision_suffix')),
        )

      if args.async_:
        pretty_print.Success(
            'Worker [{{bold}}{worker}{{reset}}] is {result_message} '
            'asynchronously.'.format(
                worker=worker.name, result_message=result_message
            )
        )
      else:
        if creates_revision:
          pretty_print.Success(
              messages_util.GetSuccessMessageForWorkerDeploy(
                  worker, args.no_promote
              )
          )
        else:
          pretty_print.Success(
              'Worker [{{bold}}{worker}{{reset}}] has been updated.'.format(
                  worker=worker.name
              )
          )
      return worker
