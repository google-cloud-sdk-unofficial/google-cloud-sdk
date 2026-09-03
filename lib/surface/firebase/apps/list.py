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
"""Command to list registered apps of a Firebase project."""

from googlecloudsdk.api_lib.firebase import apps as apps_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List the registered apps of a Firebase project."""

  _FORMAT = """
      table(
          displayName:label=APP_DISPLAY_NAME,
          appId:label=APP_ID,
          platform:label=PLATFORM,
          namespace:label=NAMESPACE,
          appStoreId:label=APP_STORE_ID,
          urls:label=URLS
      )
  """

  detailed_help = {
      'EXAMPLES': """\
          To list all Firebase apps in the current project, run:

            $ {command}

          To list only Android apps in a project, run:

            $ {command} --platform=android --project=my-project
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--platform',
        choices=list(apps_util.VALID_PLATFORMS),
        type=str.lower,
        help='Filter apps by platform (ios, android, web).',
    )
    parser.display_info.AddFormat(cls._FORMAT)

  def Run(self, args):
    project_id = properties.VALUES.core.project.Get(required=True)
    client = apps_util.AppsClient()
    return client.ListApps(project_id, platform=args.platform)
