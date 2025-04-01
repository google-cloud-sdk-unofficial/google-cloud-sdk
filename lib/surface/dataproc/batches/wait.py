# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

"""Batches wait command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc.poller import gce_batch_poller
from googlecloudsdk.api_lib.dataproc.poller import rm_batch_poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Wait(base.Command):
  """View the output of a batch as it runs or after it completes."""
  detailed_help = {
      'EXAMPLES':
          """\
          To see a list of all batches, run:

            $ gcloud dataproc batches list

          To view the output of "my-batch-job" in "us-central1" as it runs, run:

            $ {command} my-batch-job --region=us-central1
          """
  }

  @staticmethod
  def Args(parser):
    dataproc = dp.Dataproc(base.ReleaseTrack.GA)
    flags.AddBatchResourceArg(parser, 'wait', dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc(base.ReleaseTrack.GA)
    batch_id = args.CONCEPTS.batch.Parse()

    # Get the batch workload to obtain the resolved version.
    batch = dataproc.client.projects_locations_batches.Get(
        dataproc.messages.DataprocProjectsLocationsBatchesGetRequest(
            name=batch_id.RelativeName()
        )
    )
    if batch.runtimeConfig.version.startswith(
        '1'
    ) or batch.runtimeConfig.version.startswith('2'):
      poller = gce_batch_poller.GceBatchPoller(dataproc)
    else:
      poller = rm_batch_poller.RmBatchPoller(dataproc)

    waiter.WaitFor(
        poller,
        batch_id.RelativeName(),
        max_wait_ms=sys.maxsize,
        sleep_ms=5000,
        wait_ceiling_ms=5000,
        exponential_sleep_multiplier=1.3,
        custom_tracker=None,
        tracker_update_func=poller.TrackerUpdateFunction)
