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
"""Custom read command for AppOptimize Reports."""

from collections.abc import Mapping
from typing import Any

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps as deps_lib
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def format_money(money: Mapping[str, Any]) -> str:
  """Formats a Money struct as a string. Conversion is lossy."""
  units = money.get('units', '0')
  nanos = money.get('nanos', 0)
  currency_code = money.get('currency_code', '')

  if not nanos:
    return f'{units} {currency_code}'
  fractional = f'{nanos:09d}'.rstrip('0')
  return f'{units}.{fractional} {currency_code}'


@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
class Read(calliope_base.Command):
  """Reads an existing AppOptimize Report."""

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._client = apis.GetClientInstance('appoptimize', api_version='v1beta')
    self._messages = apis.GetMessagesModule('appoptimize', api_version='v1beta')

  @staticmethod
  def Args(parser):
    resource_spec = concepts.ResourceSpec(
        'appoptimize.projects.locations.reports',
        resource_name='report',
        projectsId=concepts.ResourceParameterAttributeConfig(
            name='project',
            help_text='Project ID of the Google Cloud project.',
            fallthroughs=[
                deps_lib.ArgFallthrough('--project'),
                deps_lib.PropertyFallthrough(properties.VALUES.core.project),
            ],
        ),
        locationsId=concepts.ResourceParameterAttributeConfig(
            name='location',
            help_text='The location id of the report resource.',
        ),
        reportsId=concepts.ResourceParameterAttributeConfig(
            name='report',
            help_text='The report ID.',
        ),
        is_positional=True,
    )
    concept_parsers.ConceptParser.ForResource(
        'report',
        resource_spec,
        'The resource name of the report to query. '
        'Format: projects/{project}/locations/{location}/reports/{report_id}',
        required=True,
    ).AddToParser(parser)

  def Run(self, args):
    """Reads an existing AppOptimize Report and prints it to the console."""

    # Disabling pytype attribute-error as dynamically generated messages are not
    # evaluated locally.
    request = self._messages.AppoptimizeProjectsLocationsReportsReadRequest(  # pytype: disable=attribute-error
        name=args.CONCEPTS.report.Parse().RelativeName(),
        readReportRequest=self._messages.ReadReportRequest(),  # pytype: disable=attribute-error
    )

    response = self._client.projects_locations_reports.Read(request)

    # If format is specified, return the response as is.
    # We use standard gcloud format in this case.
    if args.IsSpecified('format'):
      return response

    response_dict = encoding.MessageToPyValue(response)
    columns = response_dict.get('columns') or []
    rows = response_dict.get('rows') or []

    column_names = [column['name'] for column in columns]

    formatted_rows = []
    for row in rows:
      formatted_row = {}
      for column_name, val in zip(column_names, row):
        if column_name == 'cost':
          formatted_row[column_name] = format_money(val)
        else:
          formatted_row[column_name] = str(val) if val is not None else ''
      formatted_rows.append(formatted_row)

    # Default to print the response as a formatted table.
    table_format = 'table[box]({})'.format(
        ','.join(f'{column}:label="{column}"' for column in column_names)
    )
    args.GetDisplayInfo().AddFormat(table_format)
    return formatted_rows
