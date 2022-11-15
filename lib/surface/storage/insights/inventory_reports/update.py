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
"""Implementation of create command for inventory reports."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage.insights.inventory_reports import insights_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url

REQUIRED_METADATA_FIELDS = frozenset(['name', 'project'])


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Update an inventory report configuration."""

  detailed_help = {
      'DESCRIPTION': """
       Updates an inventory report configuration.
      """,
      'EXAMPLES': """
       To update the destination bucket of the inventory report config /projects/a/locations/b/reportConfigs/1234:

         $ {command} /projects/a/locations/b/reportConfigs/1234 --destination=gs://new-report-bucket/new-save-path/
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'report_config_name',
        help='Indicates the report config name.')
    flags.add_inventory_reports_flags(parser)

    metadata_fields_group = parser.add_group(mutex=True)
    metadata_fields_add_remove_group = metadata_fields_group.add_group(
        help='Add and Remove flags for metadata fields')
    flags.add_inventory_reports_metadata_fields_flag(metadata_fields_group)
    metadata_fields_add_remove_group.add_argument(
        '--add-metadata-fields',
        metavar='METADATA_FIELDS',
        type=arg_parsers.ArgList(
            choices=flags.INVENTORY_REPORTS_METADATA_FIELDS),
        help='Adds fields to the metadata_fields list.')
    metadata_fields_add_remove_group.add_argument(
        '--remove-metadata-fields',
        metavar='METADATA_FIELDS',
        type=arg_parsers.ArgList(
            choices=flags.INVENTORY_REPORTS_METADATA_FIELDS),
        help='Adds fields to the metadata_fields list.')
    # We don't addd --clear-metadata-fields because certain metadata-fields
    # like name and project must be always present.

  def Run(self, args):
    client = insights_api.InsightsApi()
    if args.add_metadata_fields or args.remove_metadata_fields:
      # Get the existing report config so that we can modify
      # the metadata_fields list.
      report_config = client.get(args.report_config_name)
      metadata_fields = set(
          report_config.objectMetadataReportOptions.metadataFields)
      if args.add_metadata_fields is not None:
        for field in args.add_metadata_fields:
          metadata_fields.add(field)
      if args.remove_metadata_fields is not None:
        for field in args.remove_metadata_fields:
          if field in REQUIRED_METADATA_FIELDS:
            raise errors.Error(
                'Cannot remove required metadata field: {}'.format(field))
          if field not in metadata_fields:
            raise errors.Error(
                'Cannot remove non-existing metadata field: {}'.format(field))
          metadata_fields.remove(field)
      metadata_fields_list = list(metadata_fields)
    elif args.metadata_fields:
      metadata_fields_list = args.metadata_fields
    else:
      # messages.ReportConfig does not accept None value.
      # This should be safe, as an empty list has no effect unless we add
      # the field to the updateMask.
      metadata_fields_list = []

    return client.update(
        args.report_config_name,
        destination_url=storage_url.storage_url_from_string(
            args.destination) if args.destination is not None else None,
        metadata_fields=metadata_fields_list,
        start_date=args.schedule_starts,
        end_date=args.schedule_repeats_until,
        frequency=args.schedule_repeats,
        csv_separator=args.csv_separator,
        csv_delimiter=args.csv_delimiter,
        csv_header=args.csv_header,
        display_name=args.display_name)
