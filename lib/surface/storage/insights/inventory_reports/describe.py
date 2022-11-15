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
"""Implementation of insights inventory-reports describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage.insights.inventory_reports import insights_api
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe an inventory report configurations."""

  detailed_help = {
      'DESCRIPTION':
          """
      Describe an inventory report configuration.
      """,
      'EXAMPLES':
          """

      Describe an inventory report configuration using the Report Config name:

        $ {command} /projects/<project-id>/locations/<location>/reportConfigs/<UUID>

      Describe the same inventory report with JSON formatting, only returning
      the "displayName" field:

        $ {command} /projects/<project-id>/locations/<location>/reportConfigs/<UUID> --format="json(displayName)"
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'report_config_name',
        help='Indicates the report config name.')

  def Run(self, args):
    return insights_api.InsightsApi().get(args.report_config_name)
