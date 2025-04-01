# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Command for reporting a virtual machine instance as faulty."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.util.apis import arg_utils

FAULT_REASONS_CHOICES = [
    'BEHAVIOR_UNSPECIFIED',
    'PERFORMANCE',
    'SILENT_DATA_CORRUPTION',
    'UNRECOVERABLE_GPU_ERROR',
]

DISRUPTION_SCHEDULE_CHOICES = ['IMMEDIATE']

DETAILED_HELP = {
    'brief': 'Report a host as faulty to start the repair process.',
    'DESCRIPTION': """\
          *{command}* is used to report a host as faulty to start the repair
          process.
        """,
    'EXAMPLES': """\
        To report a host as faulty for an instance named ``test-instance'', run:

          $ {command} test-instance --fault-reasons=behavior=SILENT_DATA_CORRUPTION,description="affecting our ML job" \
          --disruption-schedule=IMMEDIATE \
        """,
}


def _ValidateFaultReasonsBehavior(behavior_input):
  """Validates behavior field, throws exception if invalid."""
  behavior = behavior_input.upper()
  if behavior not in FAULT_REASONS_CHOICES:
    raise exceptions.InvalidArgumentException(
        'behavior', 'Invalid value {} for behavior'.format(behavior_input)
    )
  return behavior


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.UniverseCompatible
class ReportHostAsFaulty(base.SilentCommand):
  """Report a host as faulty to start the repair process."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)
    ReportHostAsFaulty._AddDisruptionSchedule(parser)
    ReportHostAsFaulty._AddFaultReasons(parser)

  @staticmethod
  def _AddDisruptionSchedule(parser):
    parser.add_argument(
        '--disruption-schedule',
        required=True,
        choices=DISRUPTION_SCHEDULE_CHOICES,
        type=arg_utils.ChoiceToEnumName,
        help="""\
        Specifies the timing for initiating the fault reporting process.
        The default value is {choices} which initiates the process right away.
        """.format(choices=DISRUPTION_SCHEDULE_CHOICES),
    )

  @staticmethod
  def _AddFaultReasons(parser):
    parser.add_argument(
        '--fault-reasons',
        type=arg_parsers.ArgDict(
            min_length=1,
            spec={
                'description': str,
                'behavior': _ValidateFaultReasonsBehavior,
            },
            required_keys=['behavior'],
        ),
        required=True,
        action='append',
        help="""\
        Specified and can include one or more of the following types:
        {choices}.
        This helps categorize the nature of the fault being reported.
        """.format(choices=FAULT_REASONS_CHOICES),
    )

  def _BuildRequest(self, args, instance_ref, client):
    fault_reasons = [
        client.messages.InstancesReportHostAsFaultyRequestFaultReason(
            behavior=arg_utils.ChoiceToEnum(
                reason.get('behavior'),
                client.messages.InstancesReportHostAsFaultyRequestFaultReason.BehaviorValueValuesEnum,
            ),
            description=reason.get('description'),
        )
        for reason in args.fault_reasons
    ]

    disruption_schedule_enum = arg_utils.ChoiceToEnum(
        args.disruption_schedule,
        client.messages.InstancesReportHostAsFaultyRequest.DisruptionScheduleValueValuesEnum,
    )

    request = client.messages.ComputeInstancesReportHostAsFaultyRequest(
        instance=instance_ref.Name(),
        project=instance_ref.project,
        zone=instance_ref.zone,
        instancesReportHostAsFaultyRequest=client.messages.InstancesReportHostAsFaultyRequest(
            disruptionSchedule=disruption_schedule_enum,
            faultReasons=fault_reasons,
        ),
    )
    return request

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client),
    )

    request = self._BuildRequest(args, instance_ref, client)

    return client.MakeRequests(
        [(client.apitools_client.instances, 'ReportHostAsFaulty', request)]
    )


ReportHostAsFaulty.detailed_help = DETAILED_HELP
