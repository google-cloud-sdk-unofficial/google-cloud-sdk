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
"""Command to get the SDK configuration for a Firebase application."""

from googlecloudsdk.api_lib.firebase import apps as apps_util
from googlecloudsdk.calliope import base


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class SdkConfig(base.DescribeCommand):
  """Get the SDK configuration for a Firebase application."""

  _FORMAT = 'json'

  detailed_help = {
      'EXAMPLES': (
          """\
          To get the SDK configuration for a Firebase Web app:

            $ {command} 1:1234567890:web:abcdef123456

          To write the raw configuration file (`google-services.json`) for a Firebase Android app:

            $ {command} 1:1234567890:android:abcdef123456 --format="value(configFileContents)" > google-services.json
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'app_id',
        help=(
            'The Firebase App ID (e.g. 1:1234567890:web:abcdef123456). The'
            ' platform (android, ios, or web) is inferred from the App ID.'
        ),
    )
    parser.display_info.AddFormat(cls._FORMAT)

  def Run(self, args):
    client = apps_util.AppsClient()
    return client.GetSdkConfig(app_id=args.app_id)
