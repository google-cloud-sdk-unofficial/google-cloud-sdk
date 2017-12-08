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

"""Wait for a job to complete."""

from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class Wait(base.Command):
  """View the output of a job as it runs or after it completes."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To view the output of a job as it runs, run:

            $ {command} job_id
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'id',
        metavar='JOB_ID',
        help='The ID of the job to wait.')

  @util.HandleHttpError
  def Run(self, args):
    client = self.context['dataproc_client']
    messages = self.context['dataproc_messages']

    job_ref = util.ParseJob(args.id, self.context)
    request = job_ref.Request()

    job = client.projects_regions_jobs.Get(request)
    # TODO(user) Check if Job is still running and fail or handle 401.

    job = util.WaitForJobTermination(
        job,
        self.context,
        message='Waiting for job completion',
        goal_state=messages.JobStatus.StateValueValuesEnum.DONE,
        stream_driver_log=True)

    log.status.Print('Job [{0}] finished successfully.'.format(args.id))

    return job
