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
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.policycontroller import utils
from googlecloudsdk.core import properties


def MakeConstraintLabel(template_name, constraint_name):
  return '{}/{}'.format(template_name, constraint_name)


def ListFleetConstraints(client, messages, project_id, verbose):
  """Generates list of fleet constraints."""
  formatted_constraints = {}

  fleet_constraints = status_api_utils.ListFleetConstraints(client, messages,
                                                            project_id)
  for constraint in fleet_constraints:
    constraint_label = MakeConstraintLabel(
        constraint.ref.constraintTemplateName,
        constraint.ref.name)

    formatted_constraint = {
        'constraint': constraint_label,
    }
    if verbose:
      formatted_constraint['memberships'] = []
      formatted_constraint['violations'] = []
    else:
      formatted_constraint['memberships'] = constraint.numMemberships or 0
      formatted_constraint['violations'] = constraint.numViolations or 0

    formatted_constraints[constraint_label] = formatted_constraint

  # Add membership names and violations to verbose output
  if verbose:
    membership_constraints = status_api_utils.ListMembershipConstraints(
        client, messages, project_id)
    for constraint in membership_constraints:
      constraint_label = MakeConstraintLabel(
          constraint.constraintRef.constraintTemplateName,
          constraint.constraintRef.name)
      if constraint_label in formatted_constraints:
        formatted_constraints[constraint_label]['memberships'].append(
            constraint.membershipRef.name)

    violations = status_api_utils.ListViolations(client, messages, project_id)
    for violation in violations:
      constraint_label = MakeConstraintLabel(
          violation.constraintRef.constraintTemplateName,
          violation.constraintRef.name)
      if constraint_label in formatted_constraints:
        formatted_constraints[constraint_label]['violations'].append({
            'membership':
                violation.membershipRef.name,
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


def ListMembershipConstraints(client, messages, project_id, memberships,
                              verbose):
  """Generates list of membership constraints."""
  formatted_constraints = {}

  membership_constraints = status_api_utils.ListMembershipConstraints(
      client, messages, project_id)
  for constraint in membership_constraints:
    if memberships and constraint.membershipRef.name not in memberships:
      continue

    constraint_label = MakeConstraintLabel(
        constraint.constraintRef.constraintTemplateName,
        constraint.constraintRef.name)
    membership_constraint_key = (constraint.membershipRef.name,
                                 constraint_label)
    formatted_constraint = {
        'constraint': constraint_label,
        'membership': constraint.membershipRef.name,
        'violations': constraint.status.numViolations or 0
    }
    if verbose:
      formatted_constraint['violations'] = []
      formatted_constraint['match'] = constraint.spec.kubernetesMatch or {}
      formatted_constraint['parameters'] = constraint.spec.parameters or {}
      formatted_constraint[
          'enforcementAction'] = utils.get_enforcement_action_label(
              messages.MembershipConstraintSpec
              .EnforcementActionValueValuesEnum(
                  constraint.spec.enforcementAction).name),
    formatted_constraints[membership_constraint_key] = formatted_constraint

  # Add violations to verbose output.
  if verbose:
    violations = status_api_utils.ListViolations(client, messages, project_id)
    for violation in violations:
      if memberships and violation.membershipRef.name not in memberships:
        continue
      constraint_label = MakeConstraintLabel(
          violation.constraintRef.constraintTemplateName,
          violation.constraintRef.name)
      membership_constraint_key = (violation.membershipRef.name,
                                   constraint_label)
      if membership_constraint_key in formatted_constraints:
        formatted_constraints[membership_constraint_key]['violations'].append({
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


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class List(calliope_base.ListCommand):
  """List Policy Controller constraints from the Policy Library.

  ## EXAMPLES

  To list all Policy Controller constraints from the Policy Library across the
  Fleet:

      $ {command}

  To include extended information in the listed constraints:

      $ {command} --verbose

  To list constraints for a specified Fleet membership:

      $ {command}
      --memberships=MEMBERSHIP
  """

  @classmethod
  def Args(cls, parser):
    calliope_base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Include extended information about constraints.',
        default=False)
    resources.AddMembershipResourceArg(
        parser,
        plural=True,
        membership_help=(
            'The membership names for which to list constraint templates, '
            'separated by commas if multiple are supplied.'))

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()
    project_id = properties.VALUES.core.project.Get(required=True)

    client = status_api_utils.GetClientInstance(
        self.ReleaseTrack())
    messages = status_api_utils.GetMessagesModule(
        self.ReleaseTrack())

    if args.memberships is not None:
      memberships = args.memberships
    else:
      memberships = []

    if memberships:
      return ListMembershipConstraints(
          client, messages, project_id,
          memberships, args.verbose)
    return ListFleetConstraints(
        client, messages, project_id, args.verbose
    )
