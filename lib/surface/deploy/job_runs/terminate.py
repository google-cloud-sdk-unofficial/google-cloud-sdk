# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Terminates a Cloud Deploy job run."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import job_run
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.core import log


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
    To terminate a job run `test-jobrun`, for delivery pipeline 'test-pipeline', release 'test-release', rollout 'test-rollout', in region 'us-central1', run:

      $ {command} test-jobrun --delivery-pipeline=test-pipeline --release=test-release --rollout=test-rollout --region=us-central1

""",
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Terminate(base.UpdateCommand):
  """Terminates a Cloud Deploy job run."""

  @staticmethod
  def Args(parser):
    resource_args.AddJobRunResourceArg(parser, positional=True)

  def Run(self, args):
    job_run_ref = args.CONCEPTS.job_run.Parse()

    log.status.Print(
        'Terminating job run {}.\n'.format(job_run_ref.RelativeName())
    )

    return job_run.JobRunsClient().Terminate(job_run_ref.RelativeName())
