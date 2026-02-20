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
    parser.display_info.AddFormat(
        'table(semantics_key:sort=1, otel_attribute_key, description)'
    )

  def Run(self, args):
    del args  # Unused.
    # TODO: b/473455439 - Fetch from catalog service when RPC is ready.
    return [
        {
            'semantics_key': 'ENVIRONMENT',
            'otel_attribute_key': 'deployment.environment.name',
            'value_mappings': [
                {
                    'semantics_value': 'PRODUCTION',
                    'otel_attribute_value': 'production',
                },
                {
                    'semantics_value': 'STAGING',
                    'otel_attribute_value': 'staging',
                },
                {
                    'semantics_value': 'TEST',
                    'otel_attribute_value': 'test',
                },
                {
                    'semantics_value': 'DEVELOPMENT',
                    'otel_attribute_value': 'development',
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
                },
                {
                    'semantics_value': 'HIGH',
                    'otel_attribute_value': 'high',
                },
                {
                    'semantics_value': 'MEDIUM',
                    'otel_attribute_value': 'medium',
                },
                {
                    'semantics_value': 'LOW',
                    'otel_attribute_value': 'low',
                },
            ],
            'description': (
                'Criticality level of a resource for business operational'
                ' continuity.'
            ),
        },
        {
            'semantics_key': 'COST_CENTER',
            'otel_attribute_key': 'service.cost_center',
            'value_mappings': [],
            'description': 'Cost center associated with a resource.',
        },
        {
            'semantics_key': 'BUSINESS_UNIT',
            'otel_attribute_key': 'service.business_unit',
            'value_mappings': [],
            'description': (
                'Business unit or department responsible for a resource.'
            ),
        },
    ]
