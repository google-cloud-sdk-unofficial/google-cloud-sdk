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
"""Command to submit a specified Batch job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.batch import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.batch import resource_args
from googlecloudsdk.core import log


class Submit(base.Command):
  """Submit a Batch job.

  This command can fail for the following reasons:
  * The active account does not have permission to create the Batch job.

  ## EXAMPLES

  To submit the job with config.json sample config file and name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config config.json
  """

  @staticmethod
  def Args(parser):
    resource_args.AddJobResourceArgs(parser)

    parser.add_argument(
        '--config', required=True, help='The config file of a job.')

  def Run(self, args):
    job_ref = args.CONCEPTS.job.Parse()
    job_id = job_ref.RelativeName().split('/')[-1]
    location_ref = job_ref.Parent()

    client = jobs.JobsClient()

    resp = client.Create(job_id, location_ref, args.config)
    log.status.Print(
        'Job {jobName} was successfully submitted.'.format(jobName=resp.uid))
    return resp
