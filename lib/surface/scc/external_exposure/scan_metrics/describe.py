# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command to describe external exposure scan metrics."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.external_exposure import flags
from googlecloudsdk.command_lib.scc.external_exposure import utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Describe the scan metrics for a given parent resource and location."""

  detailed_help = {
      'DESCRIPTION': (
          """\
      Returns the scan metrics for a given organization, folder, or project and location.
      """
      ),
      'EXAMPLES': (
          """\
        To describe the scan metrics for an organization, run:
          $ {command} --organization=12345 --location=global \n
        To describe the scan metrics for a folder, run:
          $ {command} --folder=12345 --location=global \n
        To describe the scan metrics for a project, run:
          $ {command} --project=12345 --location=global \n
      """
      ),
  }

  @staticmethod
  def Args(parser):
    flags.ExtractRequiredFlags(parser)

  def Run(self, args):
    path = utils.GenerateParent(args) + '/scanMetrics'
    client = utils.GetClient()
    message_module = utils.GetMessagesModule()
    if args.organization:
      request = message_module.ExternalexposureOrganizationsLocationsGetScanMetricsRequest(
          name=path
      )
      return client.organizations_locations.GetScanMetrics(request)
    elif args.folder:
      request = (
          message_module.ExternalexposureFoldersLocationsGetScanMetricsRequest(
              name=path
          )
      )
      return client.folders_locations.GetScanMetrics(request)
    elif args.project:
      request = (
          message_module.ExternalexposureProjectsLocationsGetScanMetricsRequest(
              name=path
          )
      )
      return client.projects_locations.GetScanMetrics(request)
