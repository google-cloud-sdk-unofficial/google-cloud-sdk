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
"""Command for running jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core.console import progress_tracker


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Run(base.Command):
  """Run a job."""

  detailed_help = {
      'DESCRIPTION':
          """
          {description}
          """,
      'EXAMPLES':
          """
          To run a job:

              $ {command} my-job
          """,
  }

  @staticmethod
  def Args(parser):
    job_presentation = presentation_specs.ResourcePresentationSpec(
        'JOB',
        resource_args.GetJobResourceSpec(prompt=True),
        'Job to run.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([job_presentation]).AddToParser(parser)
    polling_group = parser.add_mutually_exclusive_group()
    flags.AddAsyncFlag(polling_group)
    flags.AddWaitForCompletionFlag(polling_group)
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  def Run(self, args):
    """Run a Job on Cloud Run."""
    job_ref = args.CONCEPTS.job.Parse()
    flags.ValidateResource(job_ref)
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack())
    with serverless_operations.Connect(conn_context) as operations:
      j = operations.GetJob(job_ref)
      if j is None:
        raise serverless_exceptions.JobNotFoundError(
            'Cannot find job [{}].'.format(job_ref.Name()))
      header_msg = '{} execution...'.format(
          'Running' if args.wait else 'Starting')
      with progress_tracker.StagedProgressTracker(
          header_msg,
          stages.ExecutionStages(include_completion=args.wait),
          failure_message='Job failed',
          suppress_output=args.async_) as tracker:
        e = operations.RunJob(job_ref, args.wait, tracker, asyn=args.async_)

      if args.async_:
        pretty_print.Success(
            'Execution [{{bold}}{execution}{{reset}}] is being'
            ' started asynchronously.'.format(execution=e.name))
      else:
        operation = 'completed' if args.wait else 'started running'

        pretty_print.Success('Execution [{{bold}}{execution}{{reset}}] has '
                             'successfully {operation}.'.format(
                                 execution=e.name, operation=operation))

      log.Print(
          '\nView details about this execution by running '
          '`gcloud{release_track} run executions describe {ex_name}`.'
          '\nSee logs for this execution at: '
          # TODO(b/180749348): Don't piggyback off of cloud_run_revision
          'https://console.cloud.google.com/logs/viewer?project={project_id}&resource=cloud_run_revision/service_name/{job_name}/revision_name/{ex_name}'
          .format(
              release_track=(' {}'.format(self.ReleaseTrack().prefix)
                             if self.ReleaseTrack().prefix is not None else ''),
              project_id=job_ref.Parent().Name(),
              ex_name=e.name,
              job_name=j.name))
      return e
