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

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container.fleet.policycontroller import status_api_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import api_util as fleet_api_util
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.policycontroller import utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
import six


def FormatViolation(violation, include_membership=False):
  """Returns formatted violation from API response."""
  formatted_violation = {
      'resource_name':
          violation.resourceRef.name,
      'resource_api_group':
          violation.resourceRef.groupKind.apiGroup,
      'resource_kind':
          violation.resourceRef.groupKind.kind
  }
  if violation.resourceRef.resourceNamespace is not None:
    formatted_violation['resource_namespace'] = (
        violation.resourceRef.resourceNamespace)
  else:
    formatted_violation['resource_namespace'] = 'N/A'
  if include_membership:
    formatted_violation['membership'] = violation.membershipRef.name
  return formatted_violation


def GetMembershipConstraint(client, messages, constraint_name, project_id,
                            membership, release_track):
  """Returns a formatted membership constraint."""
  try:
    membership_obj = fleet_api_util.GetMembership(membership,
                                                  release_track)
  except apitools_exceptions.HttpNotFoundError:
    raise exceptions.Error(
        'Membership [{}] was not found in the fleet.'
        .format(membership))

  try:
    request = messages.AnthospolicycontrollerstatusPaProjectsMembershipConstraintsGetRequest(
        name='projects/{}/membershipConstraints/{}/{}'.format(
            project_id, constraint_name, membership_obj.uniqueId))
    response = client.projects_membershipConstraints.Get(request)
  except apitools_exceptions.HttpNotFoundError:
    raise exceptions.Error(
        'Constraint [{}] was not found in Fleet membership [{}].'
        .format(constraint_name, membership))

  return {
      'name':
          response.constraintRef.name,
      'template':
          response.constraintRef.constraintTemplateName,
      'enforcementAction':
          utils.get_enforcement_action_label(
              six.text_type(response.spec.enforcementAction)),
      'membership': membership,
      'violationCount':
          response.status.numViolations or 0,
      'violations': [],
      'match':
          response.spec.kubernetesMatch or {},
      'parameters':
          response.spec.parameters or {}
  }


def GetFleetConstraint(client, messages, constraint_name, project_id):
  """Returns a formatted Fleet constraint."""
  try:
    request = messages.AnthospolicycontrollerstatusPaProjectsFleetConstraintsGetRequest(
        name='projects/{}/fleetConstraints/{}'.format(
            project_id, constraint_name))
    response = client.projects_fleetConstraints.Get(request)
  except apitools_exceptions.HttpNotFoundError:
    raise exceptions.Error(
        'Constraint [{}] was not found in the fleet.'
        .format(constraint_name))
  constraint = {
      'name': response.ref.name,
      'template': response.ref.constraintTemplateName,
      'violations': [],
      'violationCount': response.numViolations or 0,
      'memberships': [],
      'membershipCount': response.numMemberships or 0
  }

  membership_constraints_request = messages.AnthospolicycontrollerstatusPaProjectsMembershipConstraintsListRequest(
      parent='projects/{}'.format(project_id))
  membership_constraints_response = client.projects_membershipConstraints.List(
      membership_constraints_request)

  for membership_constraint in membership_constraints_response.membershipConstraints:
    if constraint_name == '{}/{}'.format(
        membership_constraint.constraintRef.constraintTemplateName,
        membership_constraint.constraintRef.name):
      constraint['memberships'].append(
          membership_constraint.membershipRef.name)

  return constraint


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
        help='The constraint template name and constraint name joined by a slash, e.g. "k8srequiredlabels/all-must-have-owner".'
    )
    resources.AddMembershipResourceArg(
        parser,
        plural=True,
        membership_help=(
            'A single membership name for which to describe a membership '
            'constraint.'))

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()
    project_id = properties.VALUES.core.project.Get(required=True)

    client = status_api_utils.GetClientInstance(
        self.ReleaseTrack())
    messages = status_api_utils.GetMessagesModule(
        self.ReleaseTrack())

    constraint_name = args.CONSTRAINT_NAME.lower()

    if args.memberships is not None:
      memberships = args.memberships
      if len(memberships) != 1:
        raise exceptions.Error('Please specify a single membership name.')
      membership_name = memberships[0]
      constraint = GetMembershipConstraint(client, messages,
                                           constraint_name,
                                           project_id, membership_name,
                                           self.ReleaseTrack())
    else:
      constraint = GetFleetConstraint(client, messages, constraint_name,
                                      project_id)

    violations_request = messages.AnthospolicycontrollerstatusPaProjectsMembershipConstraintAuditViolationsListRequest(
        parent='projects/{}'.format(project_id))
    violations_response = client.projects_membershipConstraintAuditViolations.List(
        violations_request)

    # Add violations to constraint.
    if args.memberships:
      for violation in violations_response.membershipConstraintAuditViolations:
        if constraint_name == '{}/{}'.format(
            violation.constraintRef.constraintTemplateName,
            violation.constraintRef.name
        ) and violation.membershipRef.name == membership_name:
          constraint['violations'].append(FormatViolation(violation))
      return constraint
    else:
      for violation in violations_response.membershipConstraintAuditViolations:
        if constraint_name == '{}/{}'.format(
            violation.constraintRef.constraintTemplateName,
            violation.constraintRef.name):
          constraint['violations'].append(
              FormatViolation(violation, include_membership=True))

    return constraint
