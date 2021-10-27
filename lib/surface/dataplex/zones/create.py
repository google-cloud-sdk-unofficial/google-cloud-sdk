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
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import flags
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

            $ {command} projects/{project_id}/locations/{location}/lakes/{lake_id}/zones/{zone_id}
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
        },
        type=arg_utils.ChoiceToEnumName,
        help='Type', required=True)
    flags.AddDiscoveryArgs(parser)
    resource_spec = parser.add_group(
        required=True,
        help='Settings for resources attached as assets within a zone.')
    resource_spec.add_argument(
        '--resource-location-type',
        choices={
            'SINGLE_REGION': 'single_region',
            'MULTI_REGION': 'multi_region'
        },
        type=arg_utils.ChoiceToEnumName,
        help='resource location type',
        required=True)
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    zone_ref = args.CONCEPTS.zone.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    create_req_op = dataplex_client.projects_locations_lakes_zones.Create(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsLakesZonesCreateRequest(
            zoneId=zone_ref.Name(),
            parent=zone_ref.Parent().RelativeName(),
            validateOnly=args.validate_only,
            googleCloudDataplexV1Zone=zone.GenerateZoneForCreateRequest(args)))

    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete.')
      return

    async_ = getattr(args, 'async_', False)
    if not async_:
      zone.WaitForOperation(create_req_op)
      log.CreatedResource(
          zone_ref.Name(),
          details='Zone created in lake [{0}] in project [{1}] with location [{2}]'
          .format(zone_ref.lakesId, zone_ref.projectsId, zone_ref.locationsId))
      return

    log.status.Print('Creating [{0}] with operation [{1}].'.format(
        zone_ref, create_req_op.name))
