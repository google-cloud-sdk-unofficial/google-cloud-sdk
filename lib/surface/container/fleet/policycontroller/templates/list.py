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
"""List templates command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet.policycontroller import status_api_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.core import properties


def ListMembershipTemplates(
    project_id, messages, client, memberships=None, verbose=False
):
  """Generate list of formatted membership templates."""

  formatted_templates = {}

  membership_templates = status_api_utils.ListMembershipConstraintTemplates(
      client, messages, project_id
  )
  for template in membership_templates:
    if memberships and template.membershipRef.name not in memberships:
      continue

    membership_template_key = (
        template.membershipRef.name,
        template.constraintTemplateRef.name,
    )

    formatted_template = {
        'membership': template.membershipRef.name,
        'name': template.constraintTemplateRef.name,
    }

    if verbose:
      formatted_template['constraints'] = []
      formatted_template['policy_code'] = ''
      formatted_template['schema'] = template.spec.properties or {}
      formatted_template['description'] = template.description
    else:
      # This count is set after calling the membership constraints API
      formatted_template['constraints'] = 0

    for target in template.spec.targets:
      if target.target == 'admission.k8s.gatekeeper.sh':
        formatted_template['policy_code'] = target.regoPolicy.policy
        break

    formatted_templates[membership_template_key] = formatted_template

  if formatted_templates:
    membership_constraints = status_api_utils.ListMembershipConstraints(
        client, messages, project_id
    )
    for constraint in membership_constraints:
      membership_template_key = (
          constraint.membershipRef.name,
          constraint.constraintRef.constraintTemplateName,
      )
      if membership_template_key in formatted_templates:
        if verbose:
          formatted_templates[membership_template_key]['constraints'].append(
              constraint.constraintRef.name
          )
        else:
          formatted_templates[membership_template_key]['constraints'] += 1

  return [v for _, v in sorted(formatted_templates.items())]


def ListFleetTemplates(project_id, messages, client, verbose=False):
  """Generate list of formatted fleet templates."""

  formatted_templates = {}

  fleet_templates = status_api_utils.ListFleetConstraintTemplates(
      client, messages, project_id
  )
  for template in fleet_templates:
    if verbose:
      formatted_template = {
          'name': template.ref.name,
          'constraints': [],
          'memberships': [],
      }
    else:
      formatted_template = {
          'name': template.ref.name,
          'constraints': template.numConstraints or 0,
          'memberships': template.numMemberships or 0,
      }
    formatted_templates[template.ref.name] = formatted_template

  if verbose:
    membership_templates = status_api_utils.ListMembershipConstraintTemplates(
        client, messages, project_id
    )
    for template in membership_templates:
      if template.constraintTemplateRef.name in formatted_templates:
        formatted_templates[template.constraintTemplateRef.name][
            'memberships'
        ].append(template.membershipRef.name)

    fleet_constraints = status_api_utils.ListFleetConstraints(
        client, messages, project_id
    )
    for constraint in fleet_constraints:
      if constraint.ref.constraintTemplateName in formatted_templates:
        formatted_templates[constraint.ref.constraintTemplateName][
            'constraints'
        ].append(constraint.ref.name)

  return [v for _, v in sorted(formatted_templates.items())]


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class List(calliope_base.ListCommand):
  """List Policy Controller constraint templates.

  ## EXAMPLES

  To list all Policy Controller constraint templates across the fleet:

      $ {command}

  To list constraint templates with extended information:

      $ {command} --verbose

  To list constraint templates for a specified Fleet membership:

      $ {command}
      --memberships=MEMBERSHIP
  """

  @classmethod
  def Args(cls, parser):
    calliope_base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Include extended information about constraint templates.',
        default=False,
    )
    resources.AddMembershipResourceArg(
        parser,
        plural=True,
        membership_help=(
            'The membership names for which to list constraint templates, '
            'separated by commas if multiple are supplied.'
        ),
    )

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()

    project_id = properties.VALUES.core.project.Get(required=True)

    client = status_api_utils.GetClientInstance(self.ReleaseTrack())
    messages = status_api_utils.GetMessagesModule(self.ReleaseTrack())

    if args.memberships is not None:
      memberships = args.memberships
      return ListMembershipTemplates(
          project_id, messages, client, memberships, verbose=args.verbose
      )

    return ListFleetTemplates(
        project_id, messages, client, verbose=args.verbose
    )
