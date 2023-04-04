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
"""Command group for Policy Controller violations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.container.fleet.policycontroller import status_api_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import log


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class Policycontroller(calliope_base.Group):
  """Get Policy Controller audit violations."""

  pass


class ViolationCounter:
  """Track violations per membership and constraint."""

  def __init__(self):
    self.membership_constraints = []

  def Update(self, membership_name, constraint_label):
    """Adds a membership and constraint to the membership_constraints list.

    Args:
      membership_name: membership name string
      constraint_label: tuple of template name and constraint name strings
    """
    self.membership_constraints.append((membership_name, constraint_label))

  def CheckForMaxConstraintViolations(self):
    """Displays a warning if any membership constraints have >=20 violations."""
    membership_constraint_counts = collections.Counter(
        self.membership_constraints
    )
    max_violation_constraints = [
        mc for mc, count in membership_constraint_counts.items() if count >= 20
    ]

    if max_violation_constraints:
      warning_constraint_list = ''.join(
          '\n{}\t{}'.format(mc[0], mc[1]) for mc in max_violation_constraints
      )

      if len(max_violation_constraints) == 1:
        constraint_noun = 'constraint'
      else:
        constraint_noun = 'constraints'
      log.warning(
          'Maximum of 20 violations returned for the following %s. '
          + 'There may be additional violations which can be found in '
          + 'the audit Pod logs.%s',
          constraint_noun,
          warning_constraint_list,
      )


def ListMembershipViolations(
    messages,
    client,
    project_id,
    verbose=False,
    group_by=None,
    memberships=None,
    constraint_filter=None,
):
  """Lists membership constraint audit violations."""
  formatted_violations = []
  violation_counter = ViolationCounter()

  violations = status_api_utils.ListViolations(client, messages, project_id)
  for violation in violations:
    if memberships and violation.membershipRef.name not in memberships:
      continue

    constraint_label = '{}/{}'.format(
        violation.constraintRef.constraintTemplateName,
        violation.constraintRef.name,
    )

    if constraint_filter is not None and constraint_label != constraint_filter:
      continue

    formatted_violation = {
        'constraint': constraint_label,
        'membership': violation.membershipRef.name,
        'resource_kind': violation.resourceRef.groupKind.kind,
        'resource_name': violation.resourceRef.name,
        'resource_namespace': violation.resourceRef.resourceNamespace or 'N/A',
    }

    if verbose:
      formatted_violation['message'] = violation.errorMessage

    formatted_violations.append(formatted_violation)
    violation_counter.Update(violation.membershipRef.name, constraint_label)

  violation_counter.CheckForMaxConstraintViolations()

  if group_by == 'constraint' or group_by == 'membership':
    return GroupViolations(formatted_violations, group_by)

  return formatted_violations


def GroupViolations(formatted_violations, group_attribute):
  """Returns constraint or membership groups with lists of violations."""
  if group_attribute not in ('constraint', 'membership'):
    raise ValueError('group-by type must be constraint or membership')

  group_map = {}

  for formatted_violation in formatted_violations:
    if formatted_violation[group_attribute] not in group_map:
      group_map[formatted_violation[group_attribute]] = {
          group_attribute: formatted_violation[group_attribute],
          'violations': [],
      }

    group_map[formatted_violation[group_attribute]]['violations'].append(
        formatted_violation
    )

  return [v for _, v in sorted(group_map.items())]
