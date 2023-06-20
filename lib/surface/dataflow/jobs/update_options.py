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
"""Implementation of gcloud dataflow jobs update-options command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataflow import job_utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateOptions(base.Command):
  """Update pipeline options on-the-fly for running Dataflow jobs.

  This command can modify properties of running Dataflow jobs. Currently, only
  updating autoscaling settings for Streaming Engine jobs is supported.

  Adjust the autoscaling settings for Streaming Engine Dataflow jobs by
  providing at-least one of --min-num-workers or --max-num-workers (or both).
  Allow a few minutes for the changes to take effect.

  Note that autoscaling settings can only be modified on-the-fly for Streaming
  Engine jobs. Attempts to modify batch job or Streaming Appliance jobs will
  fail.


  ## EXAMPLES

  Modify autoscaling settings to scale between 5-10 workers:

    $ {command} --min-num-workers=5 --max-num-workers=10
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    job_utils.ArgsForJobRef(parser)
    parser.add_argument(
        '--min-num-workers',
        type=int,
        help=(
            'Lower-bound for autoscaling, between 1-1000. Only supported for'
            ' streaming-engine jobs.'
        ),
    )
    parser.add_argument(
        '--max-num-workers',
        type=int,
        help=(
            'Upper-bound for autoscaling, between 1-1000. Only supported for'
            ' streaming-engine jobs.'
        ),
    )

  def Run(self, args):
    """Called when the user runs gcloud dataflow jobs update-options ...

    Args:
      args: all the arguments that were provided to this command invocation.

    Returns:
      The updated Job
    """

    if args.min_num_workers is None and args.max_num_workers is None:
      raise exceptions.OneOfArgumentsRequiredException(
          ['--min_num_workers', '--max_num_workers'],
          'You must provide at-least one field to update',
      )

    job_ref = job_utils.ExtractJobRef(args)
    return apis.Jobs.UpdateOptions(
        job_ref.jobId,
        project_id=job_ref.projectId,
        region_id=job_ref.location,
        min_num_workers=args.min_num_workers,
        max_num_workers=args.max_num_workers,
    )
