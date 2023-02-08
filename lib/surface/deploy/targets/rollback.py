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
"""Rollback a Cloud Deploy target to a prior rollout."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.clouddeploy import release
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.deploy import delivery_pipeline_util
from googlecloudsdk.command_lib.deploy import exceptions as deploy_exceptions
from googlecloudsdk.command_lib.deploy import flags
from googlecloudsdk.command_lib.deploy import promote_util
from googlecloudsdk.command_lib.deploy import release_util
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.command_lib.deploy import rollout_util
from googlecloudsdk.command_lib.deploy import target_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
  To rollback a target 'prod' for delivery pipeline 'test-pipeline' in region 'us-central1', run:

  $ {command} prod --delivery-pipeline=test-pipeline --region=us-central1


""",
}
_ROLLBACK = 'rollback'


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Rollback(base.CreateCommand):
  """Rollbacks a target to a prior rollout.

  If release is not specified, the command rollbacks the target with the last
  successful deployed release. If optional rollout-id parameter is not
  specified, a generated rollout ID will be used.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddTargetResourceArg(parser, positional=True)
    flags.AddRelease(parser, 'Name of the release to rollback to.')
    flags.AddRolloutID(parser)
    flags.AddDeliveryPipeline(parser)
    flags.AddDescriptionFlag(parser)
    flags.AddAnnotationsFlag(parser, _ROLLBACK)
    flags.AddLabelsFlag(parser, _ROLLBACK)
    flags.AddStartingPhaseId(parser)

  def Run(self, args):
    target_ref = args.CONCEPTS.target.Parse()
    ref_dict = target_ref.AsDict()
    pipeline_ref = resources.REGISTRY.Parse(
        args.delivery_pipeline,
        collection='clouddeploy.projects.locations.deliveryPipelines',
        params={
            'projectsId': ref_dict['projectsId'],
            'locationsId': ref_dict['locationsId'],
            'deliveryPipelinesId': args.delivery_pipeline,
        },
    )
    pipeline_obj = delivery_pipeline_util.GetPipeline(
        pipeline_ref.RelativeName()
    )
    failed_activity_error_annotation_prefix = 'Cannot perform rollback.'
    delivery_pipeline_util.ThrowIfPipelineSuspended(
        pipeline_obj, failed_activity_error_annotation_prefix
    )
    # Check if target exists
    target_util.GetTarget(target_ref)

    current_release_ref, rollback_release_ref = _GetCurrentAndRollbackRelease(
        args.release, pipeline_ref, target_ref
    )
    try:
      release_obj = release.ReleaseClient().Get(
          rollback_release_ref.RelativeName()
      )
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)
    if release_obj.abandoned:
      error_msg_annotation_prefix = 'Cannot perform rollback.'
      raise deploy_exceptions.AbandonedReleaseError(
          error_msg_annotation_prefix, rollback_release_ref.RelativeName()
      )
    prompt = 'Rolling back target {} to release {}.\n\n'.format(
        target_ref.Name(), rollback_release_ref.Name()
    )
    release_util.PrintDiff(
        rollback_release_ref, release_obj, target_ref.Name(), prompt
    )

    console_io.PromptContinue(cancel_on_no=True)

    rollout_description = args.description or 'Rollback from {}'.format(
        current_release_ref.Name()
    )
    return promote_util.Promote(
        rollback_release_ref,
        release_obj,
        target_ref.Name(),
        False,
        rollout_id=args.rollout_id,
        annotations=args.annotations,
        labels=args.labels,
        description=rollout_description,
        # For rollbacks, default is `stable`.
        starting_phase_id=args.starting_phase_id or 'stable',
    )


def _GetCurrentAndRollbackRelease(release_id, pipeline_ref, target_ref):
  """Gets the current deployed release and the release that will be used by promote API to create the rollback rollout."""
  if release_id:
    ref_dict = target_ref.AsDict()
    current_rollout = target_util.GetCurrentRollout(target_ref, pipeline_ref)
    current_release_ref = resources.REGISTRY.ParseRelativeName(
        resources.REGISTRY.Parse(
            current_rollout.name,
            collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts',
        )
        .Parent()
        .RelativeName(),
        collection='clouddeploy.projects.locations.deliveryPipelines.releases',
    )
    rollback_release_ref = resources.REGISTRY.Parse(
        release_id,
        collection='clouddeploy.projects.locations.deliveryPipelines.releases',
        params={
            'projectsId': ref_dict['projectsId'],
            'locationsId': ref_dict['locationsId'],
            'deliveryPipelinesId': pipeline_ref.Name(),
            'releasesId': release_id,
        },
    )
    return current_release_ref, rollback_release_ref
  else:
    prior_rollouts = rollout_util.GetValidRollBackCandidate(
        target_ref, pipeline_ref
    )
    if len(prior_rollouts) < 2:
      raise core_exceptions.Error(
          'unable to rollback target {}. Target has less than 2 rollouts.'
          .format(target_ref.Name())
      )
    current_deployed_rollout, previous_deployed_rollout = prior_rollouts

    current_release_ref = resources.REGISTRY.ParseRelativeName(
        resources.REGISTRY.Parse(
            current_deployed_rollout.name,
            collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts',
        )
        .Parent()
        .RelativeName(),
        collection='clouddeploy.projects.locations.deliveryPipelines.releases',
    )
    rollback_release_ref = resources.REGISTRY.ParseRelativeName(
        resources.REGISTRY.Parse(
            previous_deployed_rollout.name,
            collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts',
        )
        .Parent()
        .RelativeName(),
        collection='clouddeploy.projects.locations.deliveryPipelines.releases',
    )
    return current_release_ref, rollback_release_ref
