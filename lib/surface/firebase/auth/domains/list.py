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
"""Command to list Firebase Authentication authorized domains."""

from googlecloudsdk.api_lib.firebase import auth as auth_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Firebase Authentication authorized domains.

  Lists the domains that Firebase Authentication allows OAuth sign-in flows
  (such as Google Sign-In) to redirect to. Sign-in from a page served on any
  other domain fails with `auth/unauthorized-domain`.

  To authorize more domains for Google Sign-In, pass their URLs to
  `--redirect-uris` of `gcloud alpha firebase auth providers enable`.
  """

  detailed_help = {
      'EXAMPLES': """\
          To list the authorized domains of the current project:

            $ {command}

          To print only the domain names, one per line:

            $ {command} --format="value(domain)"

          To check whether a Cloud Run service's domain is authorized:

            $ {command} --filter="domain=my-service-123456789012.us-central1.run.app"
      """,
  }

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat('table(domain)')

  def Run(self, args):
    project_id = properties.VALUES.core.project.Get(required=True)
    client = auth_util.AuthConfigClient()
    return [
        {'domain': domain}
        for domain in client.ListAuthorizedDomains(project_id)
    ]
