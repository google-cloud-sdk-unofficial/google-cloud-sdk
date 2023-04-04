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
"""Describe violations command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet.policycontroller import status_api_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from surface.container.fleet.policycontroller import violations


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class Describe(calliope_base.DescribeCommand):
  """Describe Policy Controller audit violations of a constraint.

  ## EXAMPLES

  To describe audit violations for the template "k8srequiredlabels" and
  constraint "all-must-have-owner":

      $ {command} k8srequiredlabels/all-must-have-owner

  To describe audit violations for a constraint on a specified membership:
      $ {command} k8srequiredlabels/all-must-have-owner
      --memberships=MEMBERSHIP
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'CONSTRAINT_NAME',
        type=str,
        help=(
            'The constraint template name and constraint name joined '
            + 'by a slash, e.g. "k8srequiredlabels/all-must-have-owner".'
        ),
    )
    resources.AddMembershipResourceArg(
        parser,
        plural=True,
        membership_help=(
            'The membership names from which to return violations, separated '
            'by commas if multiple are supplied.'
        ),
    )

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()
    project_id = properties.VALUES.core.project.Get(required=True)

    client = status_api_utils.GetClientInstance(self.ReleaseTrack())
    messages = status_api_utils.GetMessagesModule(self.ReleaseTrack())

    constraint_name = args.CONSTRAINT_NAME.lower()

    if args.memberships is not None:
      memberships = args.memberships
      if len(memberships) != 1:
        raise exceptions.Error('Please specify a single membership name.')
      # Look up membership constraint; exception will be thrown if not found.
      constraint = status_api_utils.GetMembershipConstraint(
          client,
          messages,
          constraint_name,
          project_id,
          memberships[0],
          self.ReleaseTrack(),
      )
    else:
      memberships = []
      # Look up fleet constraint; exception will be thrown if not found.
      constraint = status_api_utils.GetFleetConstraint(
          client, messages, constraint_name, project_id
      )

    if constraint['violationCount'] == 0:
      return None

    return violations.ListMembershipViolations(
        messages,
        client,
        project_id,
        args,
        memberships=memberships,
        constraint_filter=constraint_name,
    )
