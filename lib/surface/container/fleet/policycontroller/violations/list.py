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
"""List violations command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class ViolationCounter:
  """Track violations per membership and constraint."""

  membership_constraints = []

  def __init__(self):
    pass

  def update(self, violation):
    """Adds a membership and constraint tuple to the membership_constraints list.

    Args:
      violation: dict of violation data from the API response
    """
    self.membership_constraints.append(
        (violation.membershipRef.name,
         '{}/{}'.format(violation.constraintRef.constraintTemplateName,
                        violation.constraintRef.name)))

  def check_for_max_constraint_violations(self):
    """Displays a warning if any membership constraints have >=20 violations.

    """
    membership_constraint_counts = collections.Counter(
        self.membership_constraints)
    max_violation_constraints = []
    for mc, count in membership_constraint_counts.items():
      if count >= 20:
        max_violation_constraints.append(mc)
    if max_violation_constraints:
      warning_constraint_list = ''
      for mc in max_violation_constraints:
        warning_constraint_list += '\n{}\t{}'.format(mc[0], mc[1])
      constraint_noun = 'constraint' if len(
          max_violation_constraints) == 1 else 'constraints'
      log.warning('Maximum of 20 violations returned for the following ' +
                  constraint_noun +
                  '. There may be additional violations which' +
                  ' can be found in the audit Pod logs.{}'.format(
                      warning_constraint_list))


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA,
                             calliope_base.ReleaseTrack.ALPHA)
class List(calliope_base.ListCommand):
  """List Policy Controller audit violations.

  ## EXAMPLES

  To list all Policy Controller audit violations across the Fleet:

      $ {command}
  """

  @staticmethod
  def Args(parser):
    calliope_base.URI_FLAG.RemoveFromParser(parser)
    calliope_base.PAGE_SIZE_FLAG.SetDefault(parser, 100)
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Include error message with violations.',
        default=False)
    parser.add_argument(
        '--group-by',
        type=str,
        help='If set, returns violations grouped by a common attribute. Options: constraint, membership',
        default=''
    )

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()

    if args.group_by not in ['constraint', 'membership', '']:
      raise exceptions.Error(
          'Invalid group-by parameter "{}"'.format(args.group_by))
    project_id = properties.VALUES.core.project.Get(required=True)

    client = core_apis.GetClientInstance('anthospolicycontrollerstatus_pa',
                                         'v1alpha')
    messages = core_apis.GetMessagesModule('anthospolicycontrollerstatus_pa',
                                           'v1alpha')

    violations = list_pager.YieldFromList(
        service=client.projects_membershipConstraintAuditViolations,
        request=messages.
        AnthospolicycontrollerstatusPaProjectsMembershipConstraintAuditViolationsListRequest(
            parent='projects/' + project_id),
        field='membershipConstraintAuditViolations',
        batch_size_attribute='pageSize',
        batch_size=args.page_size
    )

    formatted_violations = []
    violation_counter = ViolationCounter()

    for violation in violations:
      constraint_label = '{}/{}'.format(
          violation.constraintRef.constraintTemplateName,
          violation.constraintRef.name,
      )

      formatted_violation = {
          'constraint':
              constraint_label,
          'kind':
              violation.resourceRef.groupKind.kind,
          'membership': violation.membershipRef.name,
          'name': violation.resourceRef.name,
          'namespace': violation.resourceRef.resourceNamespace,
      }

      if args.verbose:
        formatted_violation['message'] = violation.errorMessage

      formatted_violations.append(formatted_violation)
      violation_counter.update(violation)

    violation_counter.check_for_max_constraint_violations()

    if args.group_by == 'constraint' or args.group_by == 'membership':
      return group_violations(formatted_violations, args.group_by)

    return formatted_violations


def group_violations(formatted_violations, group_attribute):
  """Returns a list of constraint or membership groups with lists of violations."""
  if group_attribute not in ['constraint', 'membership']:
    raise ValueError('group-by type must be constraint or membership')

  group_map = {}

  for formatted_violation in formatted_violations:
    if formatted_violation[group_attribute] not in group_map:
      group_map[formatted_violation[group_attribute]] = {
          group_attribute:
              formatted_violation[group_attribute],
          'violations': [],
      }

    group_map[formatted_violation[group_attribute]]['violations'].append(
        formatted_violation)

  return [v for _, v in sorted(group_map.items())]
