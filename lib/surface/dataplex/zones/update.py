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
"""`gcloud dataplex zone update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.dataplex import zone
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Updating a zone."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Dataplex Zone, run:

            $ {command} create projects/{project_id}/locations/{location}/lakes/{lake_id}/zones/{zone_id}
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddZoneResourceArg(parser, 'to Update a Zone to.')
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the create action, but don\'t actually perform it.')
    parser.add_argument('--description', help='Description of the Zone')
    parser.add_argument('--display-name', help='Display Name')
    discovery_spec = parser.add_group(
        help='Settings to manage the metadata discovery and publishing in a zone.'
    )
    discovery_spec.add_argument(
        '--discovery-enabled',
        action=arg_parsers.StoreTrueFalseAction,
        help='Whether discovery is enabled.')
    trigger = discovery_spec.add_group(
        help='Determines when discovery jobs are triggered.')
    trigger.add_argument(
        '--discovery-schedule',
        help="""Cron schedule (https://en.wikipedia.org/wiki/Cron) for running
         discovery jobs periodically. Discovery jobs must be scheduled at least
         30 minutes apart.
         To explicitly set a timezone to the cron tab, apply a prefix in the
         cron tab: "CRON_TZ=${IANA_TIME_ZONE}" or "RON_TZ=${IANA_TIME_ZONE}".
         The ${IANA_TIME_ZONE} may only be a valid string from IANA time zone
         database. For example, "CRON_TZ=America/New_York 1 * * * *", or
         "TZ=America/New_York 1 * * * *""")
    publishing = discovery_spec.add_group(
        help='Settings to manage metadata publishing from a zone.')
    metastore = publishing.add_group(
        help='Settings to manage metadata publishing to a Hive Metastore from a zone.'
    )
    metastore.add_argument(
        '--metastore-enabled',
        action=arg_parsers.StoreTrueFalseAction,
        help='Whether to publish metadata to metastore.')
    bigquery = publishing.add_group(
        help='Settings to manage metadata publishing to BigQuery from a zone.')
    bigquery.add_argument(
        '--bigquery-enabled',
        action=arg_parsers.StoreTrueFalseAction,
        help='Whether to publish metadata to BigQuery.')
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    update_mask = []
    if args.IsSpecified('description'):
      update_mask.append('description')
    if args.IsSpecified('display_name'):
      update_mask.append('displayName')
    if args.IsSpecified('labels'):
      update_mask.append('labels')
    if args.IsSpecified('discovery_enabled'):
      update_mask.append('discoverySpec.enabled')
    if args.IsSpecified('discovery_schedule'):
      update_mask.append('discoverySpec.schedule')
    if args.IsSpecified('metastore_enabled'):
      update_mask.append('discoverySpec.publishing.metastore.enabled')
    if args.IsSpecified('bigquery_enabled'):
      update_mask.append('discoverySpec.publishing.bigquery.enabled')
    zone_ref = args.CONCEPTS.zone.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    create_req_op = dataplex_client.projects_locations_lakes_zones.Patch(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsLakesZonesPatchRequest(
            name=zone_ref.RelativeName(),
            validateOnly=args.validate_only,
            updateMask=u','.join(update_mask),
            googleCloudDataplexV1Zone=zone.GenerateZoneForUpdateRequest(
                args.description, args.display_name, args.labels,
                args.discovery_enabled, args.discovery_schedule,
                args.bigquery_enabled, args.metastore_enabled)))
    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete with errors:')
      return create_req_op

    async_ = getattr(args, 'async_', False)
    if not async_:
      return zone.WaitForOperation(create_req_op)
    return create_req_op
