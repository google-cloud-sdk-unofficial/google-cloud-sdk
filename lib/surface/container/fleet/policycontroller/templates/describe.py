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
"""Describe template command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container.fleet.policycontroller import status_api_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import api_util as fleet_api_util
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties


def GetFleetTemplate(client, messages, project_id, template_name):
  """Returns a formatted fleet template."""
  try:
    fleet_template_request = messages.AnthospolicycontrollerstatusPaProjectsFleetConstraintTemplatesGetRequest(
        name='projects/{}/fleetConstraintTemplates/{}'.format(
            project_id, template_name
        )
    )
    fleet_template_response = client.projects_fleetConstraintTemplates.Get(
        fleet_template_request
    )
  except apitools_exceptions.HttpNotFoundError:
    raise exceptions.Error(
        'Constraint template [{}] was not found in the fleet.'.format(
            template_name
        )
    )
  formatted_template = {
      'name': fleet_template_response.ref.name,
      'constraints': [],
      'memberships': [],
  }

  fleet_constraints_request = messages.AnthospolicycontrollerstatusPaProjectsFleetConstraintsListRequest(
      parent='projects/{}'.format(project_id)
  )
  fleet_constraints_response = client.projects_fleetConstraints.List(
      fleet_constraints_request
  )

  for fleet_constraint in fleet_constraints_response.fleetConstraints:
    if template_name == fleet_constraint.ref.constraintTemplateName:
      formatted_template['constraints'].append(fleet_constraint.ref.name)

  membership_templates_request = messages.AnthospolicycontrollerstatusPaProjectsMembershipConstraintTemplatesListRequest(
      parent='projects/{}'.format(project_id)
  )
  membership_templates_response = (
      client.projects_membershipConstraintTemplates.List(
          membership_templates_request
      )
  )

  for (
      membership_template
  ) in membership_templates_response.membershipConstraintTemplates:
    if template_name == membership_template.constraintTemplateRef.name:
      formatted_template['memberships'].append(
          membership_template.membershipRef.name
      )

  return formatted_template


def GetMembershipTemplate(
    client, messages, project_id, membership, template_name, release_track
):
  """Returns a formatted membership template."""
  try:
    membership_obj = fleet_api_util.GetMembership(membership, release_track)
  except apitools_exceptions.HttpNotFoundError:
    raise exceptions.Error(
        'Membership [{}] was not found in the fleet.'.format(membership)
    )

  try:
    membership_template_request = messages.AnthospolicycontrollerstatusPaProjectsMembershipConstraintTemplatesGetRequest(
        name='projects/{}/membershipConstraintTemplates/{}/{}'.format(
            project_id, template_name, membership_obj.uniqueId
        )
    )
    membership_template_response = (
        client.projects_membershipConstraintTemplates.Get(
            membership_template_request
        )
    )
  except apitools_exceptions.HttpNotFoundError:
    raise exceptions.Error(
        'Constraint template [{}] was not found in Fleet membership [{}].'
        .format(template_name, membership)
    )

  formatted_template = {
      'membership': membership_template_response.membershipRef.name,
      'name': membership_template_response.constraintTemplateRef.name,
      'description': membership_template_response.description,
      'schema': membership_template_response.spec.properties or {},
      'policy_code': '',
      'constraints': [],
  }

  for target in membership_template_response.spec.targets:
    if target.target == 'admission.k8s.gatekeeper.sh':
      formatted_template['policy_code'] = target.regoPolicy.policy
      break

  membership_constraints_request = messages.AnthospolicycontrollerstatusPaProjectsMembershipConstraintsListRequest(
      parent='projects/{}'.format(project_id)
  )
  membership_constraints_response = client.projects_membershipConstraints.List(
      request=membership_constraints_request
  )
  for constraint in membership_constraints_response.membershipConstraints:
    if (
        constraint.membershipRef.name == formatted_template['membership']
        and constraint.constraintRef.constraintTemplateName
        != formatted_template['name']
    ):
      formatted_template['constraints'].append(constraint.constraintRef.name)
  return formatted_template


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class Describe(calliope_base.DescribeCommand):
  """Describe a Policy Controller constraint template.

  ## EXAMPLES

  To describe the "k8srequiredlabels" Fleet constraint template:

      $ {command} k8srequiredlabels

  To describe a specified Fleet membership template:

      $ {command} k8srequiredlabels
      --memberships=MEMBERSHIP
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'TEMPLATE_NAME', type=str, help='The constraint template name.'
    )
    resources.AddMembershipResourceArg(
        parser,
        plural=True,
        membership_help=(
            'A single membership name for which to describe a membership '
            'constraint template.'
        ),
    )

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()
    project_id = properties.VALUES.core.project.Get(required=True)
    client = status_api_utils.GetClientInstance(self.ReleaseTrack())
    messages = status_api_utils.GetMessagesModule(self.ReleaseTrack())

    template_name = args.TEMPLATE_NAME.lower()

    if args.memberships is not None:
      memberships = args.memberships
      if len(memberships) != 1:
        raise exceptions.Error('Please specify a single membership name.')
      membership_name = memberships[0]

      return GetMembershipTemplate(
          client,
          messages,
          project_id,
          membership_name,
          template_name,
          self.ReleaseTrack(),
      )
    else:
      return GetFleetTemplate(client, messages, project_id, template_name)
