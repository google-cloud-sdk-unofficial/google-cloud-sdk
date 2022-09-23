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
"""List constraints command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet.policycontroller import status_api_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet.policycontroller import utils
from googlecloudsdk.core import properties


def _make_constraint_label(template_name, constraint_name):
  return '{}/{}'.format(template_name, constraint_name)


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class List(calliope_base.ListCommand):
  """List Policy Controller constraints from the Policy Library.

  ## EXAMPLES

  To list all Policy Controller constraints from the Policy Library across the
  Fleet:

      $ {command}
  """

  @staticmethod
  def Args(parser):
    calliope_base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Include extended information about constraints.',
        default=False)

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()

    project_id = properties.VALUES.core.project.Get(required=True)

    client = status_api_utils.GetClientInstance(
        self.ReleaseTrack())
    messages = status_api_utils.GetMessagesModule(
        self.ReleaseTrack())

    formatted_constraints = {}

    request = (
        messages
        .AnthospolicycontrollerstatusPaProjectsFleetConstraintsListRequest(
            parent='projects/' + project_id))

    response = client.projects_fleetConstraints.List(request=request)

    for constraint in response.fleetConstraints:
      constraint_label = _make_constraint_label(
          constraint.ref.constraintTemplateName,
          constraint.ref.name)
      formatted_constraint = {
          'constraint': constraint_label,
          'violations': constraint.numViolations or 0,
      }
      if args.verbose:
        formatted_constraint['memberships'] = {}

      formatted_constraints[constraint_label] = formatted_constraint

    if args.verbose:
      request = (
          messages.
          AnthospolicycontrollerstatusPaProjectsMembershipConstraintsListRequest(
              parent='projects/' + project_id))
      response = client.projects_membershipConstraints.List(request=request)

      for constraint in response.membershipConstraints:
        constraint_label = _make_constraint_label(
            constraint.constraintRef.constraintTemplateName,
            constraint.constraintRef.name)
        if constraint_label in formatted_constraints:
          formatted_constraints[constraint_label]['memberships'][
              constraint.membershipRef.name] = {
                  'enforcementAction':
                      utils.get_enforcement_action_label(
                          messages.MembershipConstraintSpec
                          .EnforcementActionValueValuesEnum(
                              constraint.spec.enforcementAction).name),
                  'violations': [],
                  'match':
                      constraint.spec.kubernetesMatch or {},
                  'parameters':
                      constraint.spec.parameters or {}
              }

      request = (
          messages
          .AnthospolicycontrollerstatusPaProjectsMembershipConstraintAuditViolationsListRequest(  # pylint: disable=line-too-long
              parent='projects/' + project_id))
      response = client.projects_membershipConstraintAuditViolations.List(
          request=request)

      for violation in response.membershipConstraintAuditViolations:
        constraint_label = _make_constraint_label(
            violation.constraintRef.constraintTemplateName,
            violation.constraintRef.name)
        if constraint_label in formatted_constraints:
          formatted_constraints[constraint_label]['memberships'][
              violation.membershipRef.name]['violations'].append({
                  'resource_name':
                      violation.resourceRef.name,
                  'resource_namespace':
                      violation.resourceRef.resourceNamespace or 'N/A',
                  'resource_api_group':
                      violation.resourceRef.groupKind.apiGroup,
                  'resource_kind':
                      violation.resourceRef.groupKind.kind
              })
    return [v for _, v in sorted(formatted_constraints.items())]
