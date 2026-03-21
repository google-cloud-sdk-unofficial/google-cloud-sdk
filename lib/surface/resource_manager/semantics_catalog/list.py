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
"""List command for Semantics Catalog."""

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class List(base.ListCommand):
  """Lists all Semantics Catalog entries."""

  detailed_help = {
      'EXAMPLES': (
          """
          To list all semantics catalog entries, run:

            $ {command}
          """
      ),
  }

  @staticmethod
  def Args(parser):
    # Other argument parsing setup can go here

    # Add the default format string for the command output
    format_string = (
        'table('
        'semantics_key:sort=1, '
        'otel_attribute_key, '
        'semantic_value, '
        'otel_value, '
        'description'
        ')'
    )
    parser.display_info.AddFormat(format_string)

  def Run(self, args):
    del args  # Unused.
    # TODO: b/473455439 - Fetch from catalog service when RPC is ready.
    data = [
        {
            'semantics_key': 'ENVIRONMENT',
            'otel_attribute_key': 'deployment.environment.name',
            'value_mappings': [
                {
                    'semantics_value': 'PRODUCTION',
                    'otel_attribute_value': 'production',
                    'description': 'Production environment',
                },
                {
                    'semantics_value': 'STAGING',
                    'otel_attribute_value': 'staging',
                    'description': 'Staging environment',
                },
                {
                    'semantics_value': 'TEST',
                    'otel_attribute_value': 'test',
                    'description': 'Test environment',
                },
                {
                    'semantics_value': 'DEVELOPMENT',
                    'otel_attribute_value': 'development',
                    'description': 'Development environment',
                },
            ],
            'description': 'Specifies deployment environment of a resource.',
        },
        {
            'semantics_key': 'CRITICALITY',
            'otel_attribute_key': 'service.criticality',
            'value_mappings': [
                {
                    'semantics_value': 'MISSION_CRITICAL',
                    'otel_attribute_value': 'mission_critical',
                    'description': 'Mission critical service',
                },
                {
                    'semantics_value': 'HIGH',
                    'otel_attribute_value': 'high',
                    'description': 'High criticality service',
                },
                {
                    'semantics_value': 'MEDIUM',
                    'otel_attribute_value': 'medium',
                    'description': 'Medium criticality service',
                },
                {
                    'semantics_value': 'LOW',
                    'otel_attribute_value': 'low',
                    'description': 'Low criticality service',
                },
            ],
            'description': (
                'Criticality level of a resource for business operational'
                ' continuity.'
            ),
        }
    ]
    flattened_data = []
    for item in data:
      if item['value_mappings']:
        for mapping in item['value_mappings']:
          flattened_data.append({
              'semantics_key': item['semantics_key'],
              'otel_attribute_key': item['otel_attribute_key'],
              'semantic_value': mapping['semantics_value'],
              'otel_value': mapping['otel_attribute_value'],
              'description': mapping.get('description') or item['description'],
          })
      else:
        flattened_data.append({
            'semantics_key': item['semantics_key'],
            'otel_attribute_key': item['otel_attribute_key'],
            'semantic_value': None,
            'otel_value': None,
            'description': item['description'],
        })
    return flattened_data
