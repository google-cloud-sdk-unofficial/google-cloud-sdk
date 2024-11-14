# -*- coding: utf-8 -*- #
# Copyright 2024 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex datascans create data-discovery` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import datascan
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DataDiscovery(base.Command):
  """Create a Dataplex data discovery scan job.

  Allows users to auto discover BigQuery External and BigLake tables from
  underlying Cloud Storage buckets.
  """

  detailed_help = {
      'EXAMPLES': """\

          To create a data discovery scan `data-discovery-datascan`
          in project `test-project` located in `us-central1` on Cloud Storage bucket `test-bucket`, run:

            $ {command} data-discovery-datascan --project=test-project --location=us-central1 --data-source-resource="//storage.googleapis.com/projects/test-project/buckets/test-bucket"

          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDatascanResourceArg(
        parser, 'to create a data discovery scan for.'
    )
    parser.add_argument(
        '--description',
        required=False,
        help='Description of the data discovery scan.',
    )
    parser.add_argument(
        '--display-name',
        required=False,
        help='Display name of the data discovery scan.',
    )
    parser.add_argument(
        '--data-source-resource',
        required=True,
        help=(
            'Fully-qualified service resource name of the cloud resource bucket'
            ' that contains the data for the data discovery scan, of the form:'
            ' `//storage.googleapis.com/projects/{project_id_or_number}/buckets/{bucket_id}`.'
        ),
    )
    data_spec = parser.add_group(
        help='Data spec for the data discovery scan.',
    )
    bigquery_publishing_config_arg = data_spec.add_group(
        help=(
            'BigQuery publishing config arguments for the data discovery scan.'
        ),
    )
    bigquery_publishing_config_arg.add_argument(
        '--bigquery-publishing-table-type',
        choices={
            'EXTERNAL': """default value. GCS Cloud Storage bucket is discoverd to BigQuery External tables.""",
            'BIGLAKE': """GCS Cloud Storage bucket is discoverd to BigQuery BigLake tables.""",
        },
        help=(
            'BigQuery table type to discover the cloud resource bucket. Can be'
            ' either `EXTERNAL` or `BIGLAKE`. If not specified, the table type'
            ' will be set to `EXTERNAL`.'
        ),
    )
    bigquery_publishing_config_arg.add_argument(
        '--bigquery-publishing-connection',
        help=(
            'BigQuery connection to use for auto discovering cloud resource'
            ' bucket to BigLake tables in format'
            ' `projects/{project_id}/locations/{location_id}/connections/{connection_id}`.'
            ' Connection is required for `BIGLAKE` BigQuery publishing table'
            ' type.'
        ),
    )
    execution_spec = parser.add_group(
        help='Data discovery scan execution settings.'
    )
    trigger = execution_spec.add_group(
        mutex=True, help='Data discovery scan scheduling and trigger settings.'
    )
    trigger.add_argument(
        '--on-demand',
        type=bool,
        help=(
            'If set, the scan runs one-time shortly after data discovery scan'
            ' creation.'
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
            ' * * *`. This field is required for RECURRING scans.'
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
    setattr(args, 'scan_type', 'DISCOVERY')
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

    if getattr(args, 'validate_only', False):
      log.status.Print('Validation completed. Skipping resource creation.')
      return

    async_ = getattr(args, 'async_', False)
    if not async_:
      response = datascan.WaitForOperation(create_req_op)
      log.CreatedResource(
          response.name,
          details=(
              'Data discovery scan created in project [{0}] with location [{1}]'
              .format(datascan_ref.projectsId, datascan_ref.locationsId)
          ),
      )
      return response

    log.status.Print(
        'Creating data discovery scan with path [{0}] and operation [{1}].'
        .format(datascan_ref, create_req_op.name)
    )
    return create_req_op
