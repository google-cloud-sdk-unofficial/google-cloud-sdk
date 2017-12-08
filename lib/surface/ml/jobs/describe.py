# Copyright 2016 Google Inc. All Rights Reserved.
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
"""ml jobs describe command."""

from googlecloudsdk.api_lib.ml import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class DescribeBeta(base.DescribeCommand):
  """Describe a Cloud ML job."""

  _CONSOLE_URL = ('https://console.cloud.google.com/ml/jobs/{job_id}?'
                  'project={project}')
  _LOGS_URL = ('https://console.cloud.google.com/logs?'
               'resource=ml.googleapis.com%2Fjob_id%2F{job_id}'
               '&project={project}')

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.JOB_NAME.AddToParser(parser)

  def Run(self, args):
    job_ref = resources.REGISTRY.Parse(args.job, collection='ml.projects.jobs')
    job = jobs.JobsClient().Get(job_ref)
    self.job = job  # Hack to make the Epilog() method work.
    return job

  def Epilog(self, resources_were_displayed):
    if resources_were_displayed:
      job_id = self.job.jobId
      project = properties.VALUES.core.project.Get()
      log.status.Print(
          '\nView job in the Cloud Console at:\n' +
          self._CONSOLE_URL.format(job_id=job_id, project=project))
      log.status.Print(
          '\nView logs at:\n' +
          self._LOGS_URL.format(job_id=job_id, project=project))
