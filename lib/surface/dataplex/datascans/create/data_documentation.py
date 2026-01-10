# -*- coding: utf-8 -*- #
# Copyright 2025 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex datascans create data-documentation` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import datascan
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class DataDocumentation(base.Command):
  """Create a Dataplex data documentation scan job.

  Allows users to generate documentation for Dataplex BigQuery tables.
  """

  universe_domain = properties.VALUES.core.universe_domain.Get()
  detailed_help = {
      'EXAMPLES': """\

          To create a data documentation scan `data-documentation-datascan`
          in project `test-project` located in `us-central1` on entity `test-entity`, run:

            $ {command} data-documentation-datascan --project=test-project --location=us-central1 --data-source-resource="//bigquery.{universe_domain}/projects/test-project/datasets/test-dataset/tables/test-table"

          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDatascanResourceArg(
        parser, 'to create a data documentation scan for.'
    )
    parser.add_argument(
        '--description',
        required=False,
        help='Description of the data documentation scan.',
    )
    parser.add_argument(
        '--display-name',
        required=False,
        help='Display name of the data documentation scan.',
    )
    data_source_group = parser.add_group(
        mutex=True,
        required=True,
        help='Data source for the data documentation scan.',
    )
    data_source_group.add_argument(
        '--data-source-entity',
        help=(
            'The Dataplex entity that contains the data for the data'
            ' documentation scan, of the form:'
            ' projects/{project_id_or_number}/locations/{location_id}/lakes/{lake_id}/zones/{zone_id}/entities/{entity_id}.'
            ' Currently only BigQuery table is supported.'
        ),
    )
    data_source_group.add_argument(
        '--data-source-resource',
        help=(
            'Fully-qualified service resource name of the cloud resource that'
            ' contains the data for the data documentation scan, of the form:'
            ' //bigquery.{universe_domain}/projects/{project_id_or_number}/datasets/{dataset_id}/tables/{table_id}.'
        ),
    )
    execution_spec = parser.add_group(
        help='Data documentation scan execution settings.'
    )
    trigger = execution_spec.add_group(
        mutex=True, help='Data documentation scan trigger settings.'
    )
    trigger.add_argument(
        '--on-demand',
        type=bool,
        help=(
            'If set, the scan runs one-time shortly after data documentation'
            ' scan creation.'
        ),
    )
    trigger.add_argument(
        '--schedule',
        help=(
            'Cron schedule (https://en.wikipedia.org/wiki/Cron) for running'
            ' scans periodically. To explicitly set a timezone to the cron tab,'
            ' apply a prefix in the cron tab: "CRON_TZ=${IANA_TIME_ZONE}" or'
            ' "TZ=${IANA_TIME_ZONE}". The ${IANA_TIME_ZONE} may only be a valid'
            ' string from IANA time zone database. For example,'
            ' `CRON_TZ=America/New_York 1 * * * *` or `TZ=America/New_York 1 *'
            ' * * *`. This field is required for RECURRING scans. The argument'
            ' is only valid when --on-demand is not set.'
        ),
    )
    one_time_trigger = trigger.add_group(
        help='Data documentation scan one-time trigger settings.',
    )
    one_time_trigger.add_argument(
        '--one-time',
        action='store_true',
        default=False,
        help=(
            'If set, the data documentation scan runs once, and is auto-deleted'
            ' once the ttl_after_scan_completion expires.'
        ),
    )
    one_time_trigger.add_argument(
        '--ttl-after-scan-completion',
        help=(
            'The time to live for one-time scans. Default value is 24 hours,'
            ' minimum value is 0 seconds, and maximum value is 365 days. The'
            ' time is calculated from the data scan job completion time. If'
            ' value is set as 0 seconds, the scan will be immediately deleted'
            ' upon job completion, regardless of whether the job succeeded or'
            ' failed. The value should be a number followed by a unit suffix'
            ' "s". Example: "100s" for 100 seconds. The argument is only valid '
            'when --one-time is set.'
        ),
    )
    async_group = parser.add_group(
        mutex=True,
        required=False,
        help='At most one of --async | --validate-only can be specified.',
    )
    async_group.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help="Validate the create action, but don't actually perform it.",
    )
    base.ASYNC_FLAG.AddToParser(async_group)
    labels_util.AddCreateLabelsFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.'
  )
  def Run(self, args):
    datascan_ref = args.CONCEPTS.datascan.Parse()
    setattr(args, 'scan_type', 'DOCUMENTATION')
    dataplex_client = dataplex_util.GetClientInstance()
    create_req_op = dataplex_client.projects_locations_dataScans.Create(
        dataplex_util.GetMessageModule().DataplexProjectsLocationsDataScansCreateRequest(
            dataScanId=datascan_ref.Name(),
            parent=datascan_ref.Parent().RelativeName(),
            googleCloudDataplexV1DataScan=datascan.GenerateDatascanForCreateRequest(
                args
            ),
        )
    )

    if (args.IsSpecified('ttl_after_scan_completion')
        and not args.IsSpecified('one_time')):
      raise exceptions.InvalidArgumentException(
          '--ttl-after-scan-completion',
          'can only be specified when --one-time is set.')
    if getattr(args, 'validate_only', False):
      log.status.Print('Validation completed. Skipping resource creation.')
      return

    async_ = getattr(args, 'async_', False)
    if not async_:
      response = datascan.WaitForOperation(create_req_op)
      log.CreatedResource(
          response.name,
          details=(
              'Data documentation scan created in project [{0}] with location'
              ' [{1}]'.format(datascan_ref.projectsId, datascan_ref.locationsId)
          ),
      )
      return response

    log.status.Print(
        'Creating data documentation scan with path [{0}] and operation [{1}].'
        .format(datascan_ref, create_req_op.name)
    )
    return create_req_op
