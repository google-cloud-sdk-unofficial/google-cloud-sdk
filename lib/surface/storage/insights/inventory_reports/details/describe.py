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
"""Implementation of insights inventory-reports details describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage.insights.inventory_reports import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describes inventory reports details."""

  detailed_help = {
      'DESCRIPTION':
          """
      Describe the details of an inventory report.
      """,
      'EXAMPLES':
          """

      Describe the details of an inventory report where the
      inventory report details name is
      "projects/a/locations/b/reportConfigs/c/reportDetails/d":

        $ {command} projects/a/locations/b/reportConfigs/c/reportDetails/d

      Describe the same inventory report with JSON formatting, only returning
      the "status" field:

        $ {command} projects/a/locations/b/reportConfigs/c/reportDetails/d --format="json(status)"
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'report_details_name',
        help='Specifies the name of the report detail to describe.')

  def Run(self, args):
    report_details = insights_api.InsightsApi().get_report_details(
        args.report_details_name)
    if report_details:
      log.status.Print(
          'To download the reports, use the `gcloud storage cp` command.')
      return report_details
