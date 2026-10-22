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
"""Describe environment revision command."""

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a revision of a Managed Service for Apache Spark environment."""

  detailed_help = {
      'EXAMPLES': """\
          To describe the revision `my-rev` of the environment `my-env` in
          `us-central1`, run:

            $ {command} my-rev --environment=my-env --location=us-central1
          """,
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack(), api_version='v2')
    flags.AddEnvironmentRevisionResourceArg(
        parser, 'describe', dataproc.api_version
    )

  def Run(self, args):
    revision_ref = args.CONCEPTS.revision.Parse()
    dataproc = dp.Dataproc(
        self.ReleaseTrack(),
        api_version='v2',
        location=revision_ref.locationsId,
    )
    messages = dataproc.messages
    request = (
        messages.DataprocProjectsLocationsEnvironmentsRevisionsGetRequest(
            name=revision_ref.RelativeName()
        )
    )
    revisions = dataproc.client.projects_locations_environments_revisions
    return revisions.Get(request)
