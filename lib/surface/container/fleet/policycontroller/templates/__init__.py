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
"""Command group for Policy Controller constraint templates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.calliope import base as calliope_base


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA,
                             calliope_base.ReleaseTrack.BETA)
class Policycontroller(calliope_base.Group):
  """Get Policy Controller constraint templates."""
  pass


def list_membership_templates(project_id,
                              messages,
                              client,
                              name_filter=None):
  """Generate list of formatted membership templates."""

  formatted_templates = {}
  project_path = 'projects/' + project_id

  request = messages.AnthospolicycontrollerstatusPaProjectsMembershipConstraintTemplatesListRequest(
      parent=project_path)
  response = client.projects_membershipConstraintTemplates.List(request)

  for template in response.membershipConstraintTemplates:
    if name_filter is not None and template.constraintTemplateRef.name != name_filter:
      continue

    formatted_template = {
        'constraints': [],
        'description': template.description,
        'membership': template.membershipRef.name,
        'name': template.constraintTemplateRef.name,
        'policy_code': '',
        'schema': template.spec.properties or {},
    }

    for target in template.spec.targets:
      if target.target == 'admission.k8s.gatekeeper.sh':
        formatted_template['policy_code'] = target.regoPolicy.policy
        break

    formatted_templates[(template.constraintTemplateRef.name,
                         template.membershipRef.name)] = formatted_template

  if formatted_templates:
    request = messages.AnthospolicycontrollerstatusPaProjectsMembershipConstraintsListRequest(
        parent=project_path)

    response = client.projects_membershipConstraints.List(request)

    for constraint in response.membershipConstraints:
      if (constraint.constraintRef.constraintTemplateName,
          constraint.membershipRef.name) in formatted_templates:
        formatted_templates[(
            constraint.constraintRef.constraintTemplateName,
            constraint.membershipRef.name)]['constraints'].append(
                constraint.constraintRef.name)

  return [v for _, v in sorted(formatted_templates.items())]
