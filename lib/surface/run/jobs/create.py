# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Deploy a container to Cloud Run that will run to completion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
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
from googlecloudsdk.core import log
from googlecloudsdk.core.console import progress_tracker


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Deploy a container to Cloud Run that will run to completion."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Deploys a new job to Google Cloud Run.
          """,
      'EXAMPLES':
          """\
          To deploy a new job `my-data-transformation` on Cloud Run:

              $ {command} my-data-transformation --image=gcr.io/my/image

          You may also omit the job name. Then a prompt will be displayed
          with a suggested default value:

              $ {command} --image=gcr.io/my/image
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    # Flags not specific to any platform
    job_presentation = presentation_specs.ResourcePresentationSpec(
        'JOB',
        resource_args.GetJobResourceSpec(prompt=True),
        'Job to create.',
        required=True,
        prefixes=False)
    flags.AddImageArg(parser)
    flags.AddLabelsFlag(parser)
    flags.AddParallelismFlag(parser)
    flags.AddTasksFlag(parser)
    flags.AddMaxRetriesFlag(parser)
    flags.AddTaskTimeoutFlags(parser)
    flags.AddServiceAccountFlag(parser)
    flags.AddSetEnvVarsFlag(parser)
    flags.AddSetCloudSQLFlag(parser)
    flags.AddVpcConnectorArg(parser)
    flags.AddEgressSettingsFlag(parser)
    flags.AddSetSecretsFlag(parser)
    flags.AddMemoryFlag(parser)
    flags.AddCpuFlag(parser, managed_only=True)
    flags.AddCommandFlag(parser)
    flags.AddArgsFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    flags.AddBinAuthzPolicyFlags(parser, with_clear=False)
    flags.AddBinAuthzBreakglassFlag(parser)
    flags.AddCmekKeyFlag(parser, with_clear=False)
    flags.AddSandboxArg(parser, hidden=True)

    polling_group = parser.add_mutually_exclusive_group()
    flags.AddAsyncFlag(polling_group)
    flags.AddWaitForCompletionFlag(polling_group, implies_run_now=True)

    flags.AddRunNowFlag(parser)

    concept_parsers.ConceptParser([job_presentation]).AddToParser(parser)
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  @staticmethod
  def Args(parser):
    Create.CommonArgs(parser)

  def Run(self, args):
    """Deploy a Job to Cloud Run."""
    job_ref = args.CONCEPTS.job.Parse()
    flags.ValidateResource(job_ref)

    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack())
    changes = flags.GetJobConfigurationChanges(args)
    changes.append(
        config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack()))

    run_now = args.run_now or args.wait_for_completion
    execution = None

    with serverless_operations.Connect(conn_context) as operations:
      pretty_print.Info(
          messages_util.GetStartDeployMessage(conn_context, job_ref, 'Creating',
                                              'job'))
      if run_now:
        header_msg = 'Creating and running job...'
      else:
        header_msg = 'Creating job...'
      with progress_tracker.StagedProgressTracker(
          header_msg,
          stages.JobStages(
              run_now=run_now, include_completion=args.wait_for_completion),
          failure_message='Job failed to deploy',
          suppress_output=args.async_) as tracker:
        job = operations.CreateJob(
            job_ref, changes, tracker, asyn=(args.async_ and not run_now))
        if run_now:
          execution = operations.RunJob(job_ref, args.wait_for_completion,
                                        tracker, args.async_)

      if args.async_ and not run_now:
        pretty_print.Success('Job [{{bold}}{job}{{reset}}] is being created '
                             'asynchronously.'.format(job=job.name))
      else:
        job = operations.GetJob(job_ref)
        operation = 'been created'
        if args.wait_for_completion:
          operation += ' and completed execution [{}]'.format(execution.name)
        elif run_now:
          operation += ' and started running execution [{}]'.format(
              execution.name)

        pretty_print.Success('Job [{{bold}}{job}{{reset}}] has successfully '
                             '{operation}.'.format(
                                 job=job.name, operation=operation))

      log.Print(
          '\nView details about this job by running '
          '`gcloud{release_track} run jobs describe {job_name}`.'
          '\nSee logs for this execution at: '
          # TODO(b/180749348): Don't piggyback off of cloud_run_revision
          'https://console.cloud.google.com/logs/viewer?project={project_id}&resource=cloud_run_revision/service_name/{job_name}'
          .format(
              release_track=(' {}'.format(self.ReleaseTrack().prefix)
                             if self.ReleaseTrack().prefix is not None else ''),
              project_id=job_ref.Parent().Name(),
              job_name=job.name))
      return job
