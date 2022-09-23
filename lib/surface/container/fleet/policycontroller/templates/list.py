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
from googlecloudsdk.core import properties
from surface.container.fleet.policycontroller import templates as poco_templates


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class List(calliope_base.ListCommand):
  """List Policy Controller constraint templates.

  ## EXAMPLES

  To list all Policy Controller constraint templates across the Fleet:

      $ {command}
  """

  @staticmethod
  def Args(parser):
    calliope_base.URI_FLAG.RemoveFromParser(parser)
    calliope_base.PAGE_SIZE_FLAG.SetDefault(parser, 100)
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Include extended information about constraint templates.',
        default=False)

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()

    project_id = properties.VALUES.core.project.Get(required=True)

    client = status_api_utils.GetClientInstance(
        self.ReleaseTrack())
    messages = status_api_utils.GetMessagesModule(
        self.ReleaseTrack())

    formatted_templates = {}

    if args.verbose:
      return poco_templates.list_membership_templates(project_id, messages,
                                                      client)

    # Return fleet templates if verbose flag is not given.
    request = messages.AnthospolicycontrollerstatusPaProjectsFleetConstraintTemplatesListRequest(
        parent='projects/' + project_id)
    response = client.projects_fleetConstraintTemplates.List(request)

    for template in response.fleetConstraintTemplates:
      formatted_template = {
          'name': template.ref.name,
          'constraints': template.numConstraints or 0,
          'memberships': template.numMemberships or 0
      }
      formatted_templates[template.ref.name] = formatted_template

    return [v for _, v in sorted(formatted_templates.items())]
