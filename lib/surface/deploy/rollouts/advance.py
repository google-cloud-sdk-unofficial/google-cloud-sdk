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
"""Advances a Cloud Deploy rollout to the specified phase."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import rollout
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import delivery_pipeline_util
from googlecloudsdk.command_lib.deploy import flags
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
    To advance a rollout `test-rollout` to phase `test-phase` for delivery pipeline `test-pipeline`, release `test-release` in region `us-central1`, run:

      $ {command} test-rollout --phase-id=test-phase --delivery-pipeline=test-pipeline --release=test-release --region=us-central1

""",
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Advance(base.CreateCommand):
  """Advance a rollout to a specified phase."""
  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddRolloutResourceArg(parser, positional=True)
    flags.AddPhaseId(parser)

  def Run(self, args):
    rollout_ref = args.CONCEPTS.rollout.Parse()
    pipeline_ref = rollout_ref.Parent().Parent()
    pipeline_obj = delivery_pipeline_util.GetPipeline(
        pipeline_ref.RelativeName())
    failed_activity_msg = 'Cannot advance rollout {}.'.format(
        rollout_ref.RelativeName())
    delivery_pipeline_util.ThrowIfPipelineSuspended(pipeline_obj,
                                                    failed_activity_msg)

    log.status.Print('Advancing rollout {} to phase {}.\n'.format(
        rollout_ref.RelativeName(), args.phase_id))

    return rollout.RolloutClient().AdvanceRollout(rollout_ref.RelativeName(),
                                                  args.phase_id)
