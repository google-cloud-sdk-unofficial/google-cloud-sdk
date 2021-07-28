# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex zone create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.dataplex import zone
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Creating a zone."""

  detailed_help = {
      'EXAMPLES':
          """\
          To create a Dataplex Zone, run:

            $ {command} create projects/{project_id}/locations/{location}/lakes/{lake_id}/zones/{zone_id}
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddZoneResourceArg(parser, 'to create a Zone to.')
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the create action, but don\'t actually perform it.')
    parser.add_argument('--description', help='Description of the Zone')
    parser.add_argument('--display-name', help='Display Name')
    parser.add_argument(
        '--type',
        choices={
            'RAW': 'raw.',
            'CURATED': 'curated.',
            'TYPE_UNSPECIFIED': 'type_unspecified'
        },
        type=arg_utils.ChoiceToEnumName,
        help='Type', required=True)
    discovery_spec = parser.add_group(
        help='Settings to manage the metadata discovery and publishing in a zone.'
    )
    discovery_spec.add_argument(
        '--discovery-enabled', help='Whether discovery is enabled.')
    trigger = discovery_spec.add_group(
        help='Determines when discovery jobs are triggered.')
    trigger.add_argument(
        '--schedule',
        help="""Cron schedule (https://en.wikipedia.org/wiki/Cron)
         for running discovery jobs periodically. Discovery jobs must be
         scheduled at least 30 minutes apart. To explicitly set a timezone to
         the cron tab, apply a prefix in the cron tab: "CRON_TZ=${IANA_TIME_ZONE}"
         or "RON_TZ=${IANA_TIME_ZONE}". The ${IANA_TIME_ZONE} may only be a
         valid string from IANA time zone database. For example,
         "CRON_TZ=America/New_York 1 * * * *", or "TZ=America/New_York 1 * * * *"."""
    )
    publishing = discovery_spec.add_group(
        help='Settings to manage metadata publishing from a zone.')
    metastore = publishing.add_group(
        help='Settings to manage metadata publishing to a Hive Metastore from a zone.'
    )
    metastore.add_argument(
        '--metastore-enabled', help='Whether to publish metadata to metastore.')
    metastore.add_argument(
        '--database-name',
        help="""The name of the metastore database associated with the zone. The
           specified value is interpreted as a name template that can refer to
           ${lake_id} and ${zone_id} placeholders. If unspecified, this defaults
           to "${lake_id}_${zone_id}". The database is created in the metastore
           instance associated with the parent lake. The specified name must not
           already be in use. Upon creation, this field is updated to reflect
           the actual database name. Maximum length is 128.""")
    bigquery = publishing.add_group(
        help='Settings to manage metadata publishing to BigQuery from a zone.')
    bigquery.add_argument(
        '--bigquery-enabled', help='Whether to publish metadata to BigQuery.')
    bigquery.add_argument(
        '--dataset-name',
        help="""The name of the BigQuery dataset associated with the zone. The
           specified value is interpreted as a name template that can refer to
           ${lake_id} and ${zone_id} placeholders. If unspecified, this defaults
           to "${lake_id}_${zone_id}". The dataset is created in the project
           associated with the parent lake. The specified name must not already
           be in use. Upon creation, this field is updated to reflect the actual
           dataset name.""")
    resource_spec = parser.add_group(
        help='Settings for resources attached as assets within a zone.')
    resource_spec.add_argument(
        '--location-type',
        choices={
            'LOCATION_TYPE_UNSPECIFIED': 'LOCATION_TYPE_UNSPECIFIED',
            'SINGLE_REGION': 'single_region',
            'MULTI_REGION': 'multi_region'
        },
        type=arg_utils.ChoiceToEnumName,
        help='location type', required=True)
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    zone_ref = args.CONCEPTS.zone.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    create_req_op = dataplex_client.projects_locations_lakes_zones.Create(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsLakesZonesCreateRequest(
            zoneId=zone_ref.Name(),
            parent=zone_ref.Parent().RelativeName(),
            validateOnly=args.validate_only,
            googleCloudDataplexV1Zone=zone.GenerateZoneForCreateRequest(
                args.description, args.display_name, args.labels, args.type,
                args.discovery_enabled, args.schedule,
                args.bigquery_enabled, args.dataset_name,
                args.metastore_enabled, args.database_name,
                args.location_type)))

    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete with errors:')
      return create_req_op

    async_ = getattr(args, 'async_', False)
    if not async_:
      return zone.WaitForOperation(create_req_op)
    return create_req_op
