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
"""Implementation command for deleting inventory report configurations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage.insights.inventory_reports import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  """Delete an inventory report configuration."""

  detailed_help = {
      'DESCRIPTION':
          """
      Deletes an inventory report configuration.
      """,
      'EXAMPLES':
          """

      Delete an inventory report configuration using the report config name:

        $ {command} /projects/<project-id>/locations/<location>/reportConfigs/<UUID>
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'report_config_name',
        help='Indicates the report config name.')
    parser.add_argument(
        '--force',
        action='store_true',
        help='If set, all ReportDetails for this ReportConfig'
        ' will be deleted'
    )

  def Run(self, args):
    insights_api.InsightsApi().delete(args.report_config_name, args.force)
    log.status.Print('Deleted report config: {}'.format(
        args.report_config_name))
