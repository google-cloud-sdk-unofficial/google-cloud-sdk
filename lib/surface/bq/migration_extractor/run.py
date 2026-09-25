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
"""Implements command to run the migration extractor."""

import argparse
from googlecloudsdk.calliope import base


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class Run(base.Command):
  """Run the migration extractor."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--run-mode',
        choices=['local', 'cloud'],
        default='local',
        help='Run mode for the extractor.',
    )
    parser.add_argument(
        '--secret-id',
        help='Secret ID for argument encryption.',
    )
    parser.add_argument(
        '--zone',
        help='Zone to launch Compute Engine instance.',
    )
    parser.add_argument(
        '--location',
        help='Default location.',
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Cloud Storage target (gs://bucket/path).',
    )
    parser.add_argument(
        '--gce-instance',
        help='Name of the Compute Engine instance.',
    )
    parser.add_argument(
        '--gce-startup-script-url',
        help='URL to startup script.',
    )
    parser.add_argument(
        '--expected-owner',
        help='Expected owner project of Cloud Storage bucket.',
    )
    parser.add_argument(
        '--gce-service-account',
        help='Service account for Compute Engine instance.',
    )
    parser.add_argument(
        '--service-account-user',
        help='User to grant serviceAccountUser role.',
    )
    parser.add_argument(
        '--network',
        help='Network for Compute Engine instance.',
    )
    parser.add_argument(
        '--subnet',
        help='Subnet for Compute Engine instance.',
    )
    parser.add_argument(
        '--no-address',
        action='store_true',
        help='Do not assign external IP to Compute Engine instance.',
    )
    parser.add_argument(
        '--connector',
        required=True,
        help='Connector to use for extraction.',
    )
    parser.add_argument(
        'dumper_args',
        nargs=argparse.REMAINDER,
        help='Arguments forwarded to the dumper.',
    )

  def Run(self, args):
    # TODO: b/540961765 - Implement execution logic
    pass
