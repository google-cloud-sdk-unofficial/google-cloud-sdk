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
"""Implementation of gcloud dataflow jobs resume command."""

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import job_utils
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.Hidden
class Resume(base.Command):
  """Starts resuming all given jobs.

  Once resume is triggered, if eligible, the job will enter the
  `JOB_STATE_RUNNING` state if the operation is successful. If the operation is
  not successful or the job is already running, the job state will be unchanged.
  """

  @staticmethod
  def Args(parser):
    job_utils.ArgsForJobRefs(parser, nargs='+')

  def Run(self, args):
    for job_ref in job_utils.ExtractJobRefs(args):
      try:
        apis.Jobs.Resume(
            job_ref.jobId,
            project_id=job_ref.projectId,
            region_id=job_ref.location,
        )
        log.status.Print(f'Started resuming job [{job_ref.jobId}]')
      except exceptions.HttpException as error:
        log.status.Print(
            f'Failed to resume job [{job_ref.jobId}]:'
            f' {error.payload.status_message} Ensure that you have permission'
            ' to access the job and that the `--region` flag,'
            f" {job_ref.location}, matches the job's region."
        )
