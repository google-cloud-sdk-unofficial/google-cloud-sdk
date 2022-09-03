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
"""List policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties


ENFORCEMENT_ACTION_LABEL_MAP = {
    'ENFORCEMENT_ACTION_UNSPECIFIED': 'UNSPECIFIED',
    'ENFORCEMENT_ACTION_DENY': 'DENY',
    'ENFORCEMENT_ACTION_DRYRUN': 'DRYRUN',
    'ENFORCEMENT_ACTION_WARN': 'WARN'
}


def get_enforcement_action_label(enforcement_action):
  if enforcement_action in ENFORCEMENT_ACTION_LABEL_MAP:
    return ENFORCEMENT_ACTION_LABEL_MAP[enforcement_action]
  return ENFORCEMENT_ACTION_LABEL_MAP['ENFORCEMENT_ACTION_UNSPECIFIED']


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA,
                             calliope_base.ReleaseTrack.BETA)
class List(calliope_base.ListCommand):
  """List Policy Controller constraints.

  ## EXAMPLES

  To list all Policy Controller constraints across the Fleet:

      $ {command}
  """

  @staticmethod
  def Args(parser):
    calliope_base.URI_FLAG.RemoveFromParser(parser)
    calliope_base.PAGE_SIZE_FLAG.SetDefault(parser, 100)
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Include extended information about constraints.',
        default=False)

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()

    project_id = properties.VALUES.core.project.Get(required=True)

    client = core_apis.GetClientInstance('anthospolicycontrollerstatus_pa',
                                         'v1alpha')
    messages = core_apis.GetMessagesModule('anthospolicycontrollerstatus_pa',
                                           'v1alpha')

    formatted_constraints = {}

    fleet_constraints = list_pager.YieldFromList(
        service=client.projects_fleetConstraints,
        request=messages.
        AnthospolicycontrollerstatusPaProjectsFleetConstraintsListRequest(
            parent='projects/' + project_id),
        field='fleetConstraints',
        batch_size_attribute='pageSize',
        batch_size=args.page_size
    )

    for constraint in fleet_constraints:
      formatted_constraint = {
          'name': constraint.ref.name,
          'template': constraint.ref.constraintTemplateName,
          'violations': constraint.numViolations or 0,
      }
      if args.verbose:
        formatted_constraint['memberships'] = {}

      formatted_constraints[key_from_constraint_ref(
          constraint.ref)] = formatted_constraint

    if args.verbose:
      membership_constraints = list_pager.YieldFromList(
          service=client.projects_membershipConstraints,
          request=messages.
          AnthospolicycontrollerstatusPaProjectsMembershipConstraintsListRequest(
              parent='projects/' + project_id),
          field='membershipConstraints',
          batch_size_attribute='pageSize',
          batch_size=args.page_size
      )

      for constraint in membership_constraints:
        if key_from_constraint_ref(
            constraint.constraintRef) in formatted_constraints:
          formatted_constraints[key_from_constraint_ref(
              constraint.constraintRef
          )]['memberships'][constraint.membershipRef.name] = {
              'enforcementAction':
                  get_enforcement_action_label(
                      messages.MembershipConstraintSpec
                      .EnforcementActionValueValuesEnum(
                          constraint.spec.enforcementAction).name),
              'violations': [],
              # TODO(b/242916711) match is not showing up in the API response
              # 'match': constraint.spec.match,
              'parameters':
                  constraint.spec.parameters
          }

      violations = list_pager.YieldFromList(
          service=client.projects_membershipConstraintAuditViolations,
          request=messages.
          AnthospolicycontrollerstatusPaProjectsMembershipConstraintAuditViolationsListRequest(
              parent='projects/' + project_id),
          field='membershipConstraintAuditViolations',
          batch_size_attribute='pageSize',
          batch_size=args.page_size
      )

      for violation in violations:
        if key_from_constraint_ref(
            violation.constraintRef) in formatted_constraints:
          formatted_constraints[key_from_constraint_ref(
              violation.constraintRef)]['memberships'][
                  violation.membershipRef.name]['violations'].append({
                      'name': violation.resourceRef.name,
                      'namespace': violation.resourceRef.resourceNamespace,
                      'apiGroup': violation.resourceRef.groupKind.apiGroup,
                      'kind': violation.resourceRef.groupKind.kind
                  })
    return [v for _, v in sorted(formatted_constraints.items())]


def key_from_constraint_ref(constraint_ref):
  return (constraint_ref.name, constraint_ref.constraintTemplateName)
