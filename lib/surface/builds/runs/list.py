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
"""List PipelineRuns and TaskRuns."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudbuild.v2 import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import run_flags
from googlecloudsdk.core import resources


def _GetResultURI(resource):
  result = resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='cloudbuild.projects.locations.results',
      api_version=client_util.GA_API_VERSION)
  return result.SelfLink()


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List all Cloud Build runs in a Google Cloud project."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddUriFunc(_GetResultURI)
    run_flags.AddsRegionResourceArg(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = client_util.GetClientInstance()
    messages = client_util.GetMessagesModule()

    region_ref = args.CONCEPTS.region.Parse()
    return list_pager.YieldFromList(
        client.projects_locations_results,
        messages.CloudbuildProjectsLocationsResultsListRequest(
            parent=region_ref.RelativeName(), filter=args.filter),
        field='results',
        batch_size=args.page_size,
        batch_size_attribute='pageSize',
        limit=args.limit)
