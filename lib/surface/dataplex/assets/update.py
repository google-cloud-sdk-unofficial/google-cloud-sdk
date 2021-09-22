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
"""`gcloud dataplex asset update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import asset
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Updating an Asset."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Dataplex Asset, run:

            $ {command} projects/{project_id}/locations/{location}/lakes/{lake_id}/zones/{zone_id}/assets/{asset_id}
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddAssetResourceArg(parser, 'to update an Asset to.')
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the update action, but don\'t actually perform it.')
    parser.add_argument('--description', help='Description of the Asset')
    parser.add_argument('--display-name', help='Display Name')
    resource_spec = parser.add_group(
        help='Specification of the resource that is referenced by this asset.')
    resource_spec.add_argument(
        '--deletion-policy',
        choices={
            'DETACH_RESOURCE': 'detach resource',
            'DELETE_RESOURCE': 'delete resource',
            'DELETION_POLICY_UNSPECIFIED': 'deletion policy unspecified'
        },
        type=arg_utils.ChoiceToEnumName,
        help='Deletion policy of the attached resource.',
        default='DELETION_POLICY_UNSPECIFIED')
    discovery_spec = parser.add_group(
        help='Settings to manage the metadata discovery and publishing for an asset.'
    )
    discovery_spec.add_argument(
        '--discovery-enabled',
        action=arg_parsers.StoreTrueFalseAction,
        help='Whether discovery is enable')
    discovery_spec.add_argument(
        '--include-patterns',
        default=[],
        type=arg_parsers.ArgList(),
        metavar='INCLUDE_PATTERNS',
        help="""The list of patterns to apply for selecting data to include
        during discovery if only a subset of the data should considered. For
        Cloud Storage bucket assets, these are interpreted as glob patterns
        used to match object names. For BigQuery dataset assets, these are
        interpreted as patterns to match table names.""")
    discovery_spec.add_argument(
        '--exclude-patterns',
        default=[],
        type=arg_parsers.ArgList(),
        metavar='EXCLUDE_PATTERNS',
        help="""The list of patterns to apply for selecting data to exclude
        during discovery. For Cloud Storage bucket assets, these are interpreted
        as glob patterns used to match object names. For BigQuery dataset
        assets, these are interpreted as patterns to match table names.""")
    discovery_spec.add_argument(
        '--inheritance-mode',
        choices={
            'OVERRIDE': 'override',
            'INHERIT': 'inherit',
            'INHERITANCE_MODE_UNSPECIFIED': 'inheritance mode unspecified'
        },
        type=arg_utils.ChoiceToEnumName,
        default='INHERITANCE_MODE_UNSPECIFIED',
        help='Options for how fields within this configuration can be inherited.'
    )
    trigger = discovery_spec.add_group(
        help='Determines when discovery jobs are triggered.')
    trigger.add_argument(
        '--discovery-schedule',
        help="""Cron schedule (https://en.wikipedia.org/wiki/Cron) for running
                discovery jobs periodically. Discovery jobs must be scheduled at
                least 30 minutes apart."""
    )
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
    if args.IsSpecified('include_patterns'):
      update_mask.append('discoverySpec.includePatterns')
    if args.IsSpecified('exclude_patterns'):
      update_mask.append('discoverySpec.excludePatterns')
    if args.IsSpecified('inheritance_mode'):
      update_mask.append('discoverySpec.inheritanceMode')
    if args.IsSpecified('deletion_policy'):
      update_mask.append('resourceSpec.deletion_policy')
    if args.IsSpecified('discovery_schedule'):
      update_mask.append('discoverySpec.schedule')
    asset_ref = args.CONCEPTS.asset.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    message = dataplex_util.GetMessageModule()
    create_req_op = dataplex_client.projects_locations_lakes_zones_assets.Patch(
        message.DataplexProjectsLocationsLakesZonesAssetsPatchRequest(
            name=asset_ref.RelativeName(),
            validateOnly=args.validate_only,
            updateMask=u','.join(update_mask),
            googleCloudDataplexV1Asset=message.GoogleCloudDataplexV1Asset(
                description=args.description,
                displayName=args.display_name,
                labels=dataplex_util.CreateLabels(
                    message.GoogleCloudDataplexV1Asset, args),
                resourceSpec=message.GoogleCloudDataplexV1AssetResourceSpec(
                    deletionPolicy=message
                    .GoogleCloudDataplexV1AssetResourceSpec
                    .DeletionPolicyValueValuesEnum(args.deletion_policy)),
                discoverySpec=message.GoogleCloudDataplexV1AssetDiscoverySpec(
                    enabled=args.discovery_enabled,
                    includePatterns=args.include_patterns,
                    excludePatterns=args.exclude_patterns,
                    inheritanceMode=message
                    .GoogleCloudDataplexV1AssetDiscoverySpec
                    .InheritanceModeValueValuesEnum(args.inheritance_mode),
                    schedule=args.discovery_schedule))))
    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete with errors:')
      return create_req_op

    async_ = getattr(args, 'async_', False)
    if not async_:
      return asset.WaitForOperation(create_req_op)
    return create_req_op
