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
"""Describe constraint command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet.policycontroller import status_api_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties


def FormatViolation(violation, include_membership=False):
  """Returns formatted violation from API response."""
  formatted_violation = {
      'resource_name': violation.resourceRef.name,
      'resource_api_group': violation.resourceRef.groupKind.apiGroup,
      'resource_kind': violation.resourceRef.groupKind.kind,
  }
  if violation.resourceRef.resourceNamespace is not None:
    formatted_violation['resource_namespace'] = (
        violation.resourceRef.resourceNamespace
    )
  else:
    formatted_violation['resource_namespace'] = 'N/A'
  if include_membership:
    formatted_violation['membership'] = violation.membershipRef.name
  return formatted_violation


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class Describe(calliope_base.DescribeCommand):
  """Describe a Policy Controller constraint from the Policy Library.

  ## EXAMPLES

  To describe the "all-must-have-owner" Fleet constraint for the template
  "k8srequiredlabels":

      $ {command} k8srequiredlabels/all-must-have-owner

  To describe the "all-must-have-owner" membership constraint for the template
  "k8srequiredlabels" for a membership:

      $ {command} k8srequiredlabels/all-must-have-owner
      --memberships=MEMBERSHIP
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'CONSTRAINT_NAME',
        type=str,
        help=(
            'The constraint template name and constraint name joined by a'
            ' slash, e.g. "k8srequiredlabels/all-must-have-owner".'
        ),
    )
    resources.AddMembershipResourceArg(
        parser,
        plural=True,
        membership_help=(
            'A single membership name for which to describe a membership '
            'constraint.'
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
      membership_name = memberships[0]
      constraint = status_api_utils.GetMembershipConstraint(
          client,
          messages,
          constraint_name,
          project_id,
          membership_name,
          self.ReleaseTrack(),
      )
    else:
      constraint = status_api_utils.GetFleetConstraint(
          client, messages, constraint_name, project_id
      )

    violations_request = messages.AnthospolicycontrollerstatusPaProjectsMembershipConstraintAuditViolationsListRequest(
        parent='projects/{}'.format(project_id)
    )
    violations_response = (
        client.projects_membershipConstraintAuditViolations.List(
            violations_request
        )
    )

    # Add violations to constraint.
    if args.memberships:
      for violation in violations_response.membershipConstraintAuditViolations:
        if (
            constraint_name
            == '{}/{}'.format(
                violation.constraintRef.constraintTemplateName,
                violation.constraintRef.name,
            )
            and violation.membershipRef.name == membership_name
        ):
          constraint['violations'].append(FormatViolation(violation))
      return constraint
    else:
      for violation in violations_response.membershipConstraintAuditViolations:
        if constraint_name == '{}/{}'.format(
            violation.constraintRef.constraintTemplateName,
            violation.constraintRef.name,
        ):
          constraint['violations'].append(
              FormatViolation(violation, include_membership=True)
          )

    return constraint
