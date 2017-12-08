# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Implementation of gcloud dataflow jobs drain command.
"""

from apitools.base.py import exceptions

from googlecloudsdk.api_lib.dataflow import dataflow_util
from googlecloudsdk.api_lib.dataflow import job_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from surface import dataflow as commands


@base.Hidden
class Drain(base.Command):
  """Drains all jobs that match the command line arguments.

     Once Drain is triggered, the pipeline will stop accepting new inputs.
     The input watermark will be advanced to infinity. Elements already in the
     pipeline will continue to be processed. Drained jobs can safely be
     cancelled.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    job_utils.ArgsForJobRefs(parser, nargs='+')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: all the arguments that were provided to this command invocation.
    """
    drained = []
    failed = []
    output_stream = log.status.GetConsoleWriterStream()
    for job_ref in job_utils.ExtractJobRefs(self.context, args):
      output_stream.flush()
      try:
        output_stream.write('Starting drain for job \'{0}\' ... '
                            .format(job_ref.jobId))
        self._DrainJob(job_ref)
        output_stream.write('Success\n')
        drained.append(job_ref.jobId)
      except exceptions.HttpError as error:
        reason = dataflow_util.GetErrorMessage(error)
        output_stream.write('Failure: {0}\n'.format(reason))
        failed.append(job_ref.jobId)
    if drained:
      log.status.Print('Started draining jobs: [{0}]'.format(','.join(drained)))
    if failed:
      log.status.Print('Failed to start draining jobs: [{0}]'
                       .format(','.join(failed)))

  def _DrainJob(self, job_ref):
    """Drains a job.

    Args:
      job_ref: resources.Resource, The reference to the job to drain.
    """
    apitools_client = self.context[commands.DATAFLOW_APITOOLS_CLIENT_KEY]
    dataflow_messages = self.context[commands.DATAFLOW_MESSAGES_MODULE_KEY]

    request = dataflow_messages.DataflowProjectsJobsUpdateRequest(
        projectId=job_ref.projectId,
        jobId=job_ref.jobId,
        # We don't need to send the full job, because only the state can be
        # updated, and the other fields are ignored.
        job=dataflow_messages.Job(
            requestedState=(dataflow_messages.Job.RequestedStateValueValuesEnum
                            .JOB_STATE_DRAINED)))

    try:
      apitools_client.projects_jobs.Update(request)
    except exceptions.HttpError as error:
      raise error
