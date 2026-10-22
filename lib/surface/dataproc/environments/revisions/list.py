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
"""List environment revisions command."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List the revisions of a Managed Service for Apache Spark environment."""

  detailed_help = {
      'DESCRIPTION': """\
          List the revisions of a Managed Service for Apache Spark environment.

          An optional filter can be used to constrain the revisions returned.
          The filter is evaluated by the service using the syntax described in
          https://google.aip.dev/160. Supported fields are `revision_id`,
          `uid`, `state`, and `create_time`. `revision_id` is the last segment
          of the revision resource name. `state` can be one of `ACTIVE` or
          `FAILED`. `create_time` takes an RFC 3339 timestamp, for example
          `"2026-01-01T00:00:00Z"`.
          """,
      'EXAMPLES': """\
          To list the revisions of the environment `my-env` in `us-central1`,
          run:

            $ {command} --environment=my-env --location=us-central1

          To list only the revisions of `my-env` that were built successfully,
          run:

            $ {command} --environment=my-env --location=us-central1 \\
                --filter="state = ACTIVE"
          """,
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack(), api_version='v2')
    flags.AddEnvironmentResourceArg(
        parser, 'list revisions of', dataproc.api_version, positional=False
    )
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat("""
          table(
            name.basename():label=REVISION_ID,
            environment.state:label=STATE,
            firstof(environment.baseVersion,
                    environment.status.baseVersion):label=BASE_VERSION,
            environment.baseEnvironment.basename():label=BASE_ENVIRONMENT,
            createTime:label=CREATE_TIME
          )
    """)

  def Run(self, args):
    environment_ref = args.CONCEPTS.environment.Parse()
    dataproc = dp.Dataproc(
        self.ReleaseTrack(),
        api_version='v2',
        location=environment_ref.locationsId,
    )
    messages = dataproc.messages
    request = (
        messages.DataprocProjectsLocationsEnvironmentsRevisionsListRequest(
            parent=environment_ref.RelativeName()
        )
    )
    # `--filter` is evaluated by the service. Clear `args.filter` so that gcloud
    # does not filter the results again client-side.
    # TODO(b/545765872): The service rejects any non-empty filter until AIP-160
    # filtering is rolled out.
    if args.filter:
      request.filter = args.filter
      args.filter = None

    return list_pager.YieldFromList(
        dataproc.client.projects_locations_environments_revisions,
        request,
        limit=args.limit,
        field='environmentRevisions',
        batch_size=args.page_size,
        batch_size_attribute='pageSize',
    )
