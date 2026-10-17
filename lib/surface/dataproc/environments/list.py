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
"""List environments command."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Managed Service for Apache Spark environments."""

  detailed_help = {
      'DESCRIPTION': """\
          List Managed Service for Apache Spark environments in a location.

          An optional filter can be used to constrain the environments
          returned. The filter is evaluated by the service using the syntax
          described in https://google.aip.dev/160. Supported fields are
          `environment_id`, `uid`, `state`, `labels.[KEY]`, `create_time`,
          and `update_time`, where `[KEY]` is a label key. `environment_id`
          is the last segment of the environment resource name. `state` can
          be one of `CREATING`, `ACTIVE`, `FAILED`, or `DELETING`.
          `create_time` and `update_time` take RFC 3339 timestamps, for
          example `"2026-01-01T00:00:00Z"`.
          """,
      'EXAMPLES': """\
          To list all environments in `us-central1`, run:

            $ {command} --location=us-central1

          To list only the active environments in `us-central1`, run:

            $ {command} --location=us-central1 --filter="state = ACTIVE"

          To list the environments in `us-central1` that have the label
          `env=prod`, run:

            $ {command} --location=us-central1 --filter='labels.env = "prod"'
          """,
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack(), api_version='v2')
    flags.AddEnvironmentLocationResourceArg(
        parser, 'list environments', dataproc.api_version
    )
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat("""
          table(
            name.basename():label=NAME,
            state:label=STATE,
            revisionId:label=REVISION_ID,
            firstof(baseVersion, status.baseVersion):label=BASE_VERSION,
            baseEnvironment.basename():label=BASE_ENVIRONMENT,
            updateTime:label=UPDATE_TIME
          )
    """)

  def Run(self, args):
    location_ref = args.CONCEPTS.location.Parse()
    dataproc = dp.Dataproc(
        self.ReleaseTrack(),
        api_version='v2',
        location=location_ref.locationsId,
    )
    request = (
        dataproc.messages.DataprocProjectsLocationsEnvironmentsListRequest(
            parent=location_ref.RelativeName()
        )
    )
    # `--filter` is evaluated by the service. Clear `args.filter` so that gcloud
    # does not filter the results again client-side.
    # TODO(b/545765872): The service rejects any non-empty filter until AIP-160
    # filtering is rolled out. Verify the documented filter fields then.
    if args.filter:
      request.filter = args.filter
      args.filter = None

    return list_pager.YieldFromList(
        dataproc.client.projects_locations_environments,
        request,
        limit=args.limit,
        field='environments',
        batch_size=args.page_size,
        batch_size_attribute='pageSize',
    )
