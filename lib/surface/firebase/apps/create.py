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
"""Command to create a Firebase application."""

from googlecloudsdk.api_lib.firebase import apps as apps_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create a new Firebase application."""

  _FORMAT = 'yaml'

  detailed_help = {
      'EXAMPLES': """\
          To create an Android app with package name `com.example.app`:

            $ {command} --platform=android --package-name=com.example.app --display-name="My Android App"

          To create an iOS app with bundle ID `com.example.app`:

            $ {command} --platform=ios --bundle-id=com.example.app --display-name="My iOS App"

          To create a Web app:

            $ {command} --platform=web --display-name="My Web App"
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--platform',
        choices=list(apps_util.VALID_PLATFORMS),
        type=str.lower,
        required=True,
        help='The platform of the app to create (android, ios, web).',
    )
    parser.add_argument(
        '--display-name',
        help='The user-assigned display name of the App.',
    )
    parser.add_argument(
        '--package-name',
        help='The package name for the Android app (e.g. com.example.my_app).',
    )
    parser.add_argument(
        '--bundle-id',
        help='The canonical bundle ID of the iOS app as it would appear in the iOS App Store.',
    )
    parser.add_argument(
        '--app-store-id',
        help='The App Store ID for the iOS app.',
    )
    parser.display_info.AddFormat(cls._FORMAT)

  def Run(self, args):
    if args.platform == 'android':
      if not args.package_name:
        raise calliope_exceptions.RequiredArgumentException(
            '--package-name',
            '--package-name is required when creating an Android app.',
        )
      if args.bundle_id:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--bundle-id', '--platform=android'
        )
      if args.app_store_id:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--app-store-id', '--platform=android'
        )
    elif args.platform == 'ios':
      if not args.bundle_id:
        raise calliope_exceptions.RequiredArgumentException(
            '--bundle-id',
            '--bundle-id is required when creating an iOS app.',
        )
      if args.package_name:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--package-name', '--platform=ios'
        )
    elif args.platform == 'web':
      if args.package_name:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--package-name', '--platform=web'
        )
      if args.bundle_id:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--bundle-id', '--platform=web'
        )
      if args.app_store_id:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--app-store-id', '--platform=web'
        )

    project_id = properties.VALUES.core.project.Get(required=True)
    client = apps_util.AppsClient()

    result = client.CreateApp(
        project_id=project_id,
        platform=args.platform,
        display_name=args.display_name,
        package_name=args.package_name,
        bundle_id=args.bundle_id,
        app_store_id=args.app_store_id,
    )

    app_id = result.get('appId')
    if app_id:
      log.CreatedResource(app_id, kind='App')
    return result
