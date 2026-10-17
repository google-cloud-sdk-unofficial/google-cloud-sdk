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


from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataflow import job_utils


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class UpdateOptions(base.Command):
  """Update pipeline options on-the-fly for running Dataflow jobs.

  This command can modify properties of running Dataflow jobs. Currently, only
  updating autoscaling settings for Streaming Engine jobs is supported.

  Adjust the autoscaling settings for Streaming Engine Dataflow jobs by
  providing at-least one of --min-num-workers or --max-num-workers or
  --worker-utilization-hint (or all 3), or --unset-worker-utilization-hint
  (which cannot be run at the same time as --worker-utilization-hint but works
  with the others).
  Allow a few minutes for the changes to take effect.

  Note that autoscaling settings can only be modified on-the-fly for Streaming
  Engine jobs. Attempts to modify batch job or Streaming Appliance jobs will
  fail.


  ## EXAMPLES

  Modify autoscaling settings to scale between 5-10 workers:

    $ {command} --min-num-workers=5 --max-num-workers=10

  Require a job to use at least 2 workers:

    $ {command} --min-num-workers=2

  Require a job to use at most 20 workers:

    $ {command} --max-num-workers=20

  Adjust the hint of target worker utilization to 70% for horizontal
  autoscaling:

    $ {command} --worker-utilization-hint=0.7

  "Unset" worker utilization hint so that horizontal scaling will rely on its
  default CPU utilization target:

    $ {command} --unset-worker-utilization-hint
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
    utilization_group = parser.add_mutually_exclusive_group()
    utilization_group.add_argument(
        '--worker-utilization-hint',
        type=float,
        help=(
            'Target CPU utilization for autoscaling, ranging from 0.1 to 0.9.'
            ' Only supported for streaming-engine jobs with autoscaling'
            ' enabled.'
        ),
    )
    utilization_group.add_argument(
        '--unset-worker-utilization-hint',
        action='store_true',
        help=(
            'Unset --worker-utilization-hint. This causes the'
            ' job autoscaling to fall back to internal tunings'
            ' if they exist, or otherwise use the default hint value.'
        ),
    )

    latency_group = parser.add_mutually_exclusive_group(hidden=True)
    latency_group.add_argument(
        '--latency-tier',
        type=str,
        choices=['low_latency', 'medium_latency', 'high_latency'],
        hidden=True,
        help=(
            'Latency tier for the job. Options are "low_latency", '
            '"medium_latency", or "high_latency". Only supported for'
            ' streaming-engine jobs with autoscaling enabled.'
        ),
    )
    latency_group.add_argument(
        '--unset-latency-tier',
        action='store_true',
        hidden=True,
        help=(
            'Unset --latency-tier. This causes the job to fall back to'
            ' internal tunings.'
        ),
    )

    schedule_group = parser.add_mutually_exclusive_group()
    schedule_group.add_argument(
        '--set-schedule',
        type=str,
        help=(
            'Unique identifier for the autoscaling schedule to create or'
            ' update.'
        ),
    )
    schedule_group.add_argument(
        '--unset-schedule',
        type=str,
        help='Unique identifier of the autoscaling schedule to remove.',
    )
    schedule_group.add_argument(
        '--unset-schedules',
        action='store_true',
        help='Remove all autoscaling schedules from the job.',
    )

    parser.add_argument(
        '--autoscaling-schedule',
        type=str,
        help='Crontab expression specifying when the schedule starts.',
    )
    parser.add_argument(
        '--autoscaling-schedule-duration-seconds',
        type=int,
        help='Duration in seconds for which the schedule will be active.',
    )
    parser.add_argument(
        '--autoscaling-schedule-timezone',
        type=str,
        help=(
            'Time zone for the schedule from tz database (e.g.,'
            ' America/Los_Angeles).'
        ),
    )
    parser.add_argument(
        '--autoscaling-schedule-priority',
        type=int,
        help=(
            'Priority of the schedule. If two schedules overlap, the one with'
            ' the higher priority will be used.'
        ),
    )
    parser.add_argument(
        '--autoscaling-min-num-workers',
        '--autoscaling-min-workers',
        dest='autoscaling_min_num_workers',
        type=int,
        help='Minimum worker count when schedule is active.',
    )
    parser.add_argument(
        '--autoscaling-max-num-workers',
        '--autoscaling-max-workers',
        dest='autoscaling_max_num_workers',
        type=int,
        help='Maximum worker count when schedule is active.',
    )
    parser.add_argument(
        '--autoscaling-worker-utilization-hint',
        type=float,
        help='Target worker utilization hint when schedule is active.',
    )
    parser.add_argument(
        '--autoscaling-latency-tier',
        type=str,
        choices=['low_latency', 'medium_latency', 'high_latency'],
        hidden=True,
        help='Latency tier when schedule is active.',
    )

  def Run(self, args):
    """Called when the user runs gcloud dataflow jobs update-options ...

    Args:
      args: all the arguments that were provided to this command invocation.

    Returns:
      The updated Job
    """
    if args.set_schedule is None and (
        args.autoscaling_schedule is not None
        or args.autoscaling_schedule_duration_seconds is not None
        or args.autoscaling_schedule_timezone is not None
        or args.autoscaling_schedule_priority is not None
        or args.autoscaling_min_num_workers is not None
        or args.autoscaling_max_num_workers is not None
        or args.autoscaling_worker_utilization_hint is not None
        or args.autoscaling_latency_tier is not None
    ):
      raise exceptions.RequiredArgumentException(
          '--set-schedule',
          'You must specify --set-schedule when configuring an autoscaling'
          ' schedule.',
      )

    if (
        args.min_num_workers is None
        and args.max_num_workers is None
        and args.worker_utilization_hint is None
        and not args.unset_worker_utilization_hint
        and args.latency_tier is None
        and not args.unset_latency_tier
        and args.set_schedule is None
        and args.unset_schedule is None
        and not args.unset_schedules
    ):
      raise exceptions.OneOfArgumentsRequiredException(
          [
              '--min-num-workers',
              '--max-num-workers',
              '--worker-utilization-hint',
              '--unset-worker-utilization-hint',
              '--latency-tier',
              '--unset-latency-tier',
              '--set-schedule',
              '--unset-schedule',
              '--unset-schedules',
          ],
          'You must provide at-least one field to update',
      )

    job_ref = job_utils.ExtractJobRef(args)
    return apis.Jobs.UpdateOptions(
        job_ref.jobId,
        project_id=job_ref.projectId,
        region_id=job_ref.location,
        min_num_workers=args.min_num_workers,
        max_num_workers=args.max_num_workers,
        worker_utilization_hint=args.worker_utilization_hint,
        unset_worker_utilization_hint=args.unset_worker_utilization_hint,
        latency_tier=args.latency_tier,
        unset_latency_tier=args.unset_latency_tier,
        set_schedule=args.set_schedule,
        unset_schedule=args.unset_schedule,
        unset_schedules=args.unset_schedules,
        autoscaling_schedule=args.autoscaling_schedule,
        autoscaling_schedule_duration_seconds=args.autoscaling_schedule_duration_seconds,
        autoscaling_schedule_timezone=args.autoscaling_schedule_timezone,
        autoscaling_schedule_priority=args.autoscaling_schedule_priority,
        autoscaling_min_num_workers=args.autoscaling_min_num_workers,
        autoscaling_max_num_workers=args.autoscaling_max_num_workers,
        autoscaling_worker_utilization_hint=args.autoscaling_worker_utilization_hint,
        autoscaling_latency_tier=args.autoscaling_latency_tier,
    )
