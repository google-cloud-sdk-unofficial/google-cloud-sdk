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
"""Command to enable and configure Google Sign-In for Firebase Authentication."""

from googlecloudsdk.api_lib.firebase import auth as auth_util
from googlecloudsdk.api_lib.firebase import util as firebase_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Enable(base.Command):
  """Enable and configure Google Sign-In for Firebase Authentication."""

  detailed_help = {
      'EXAMPLES': """\
          To enable Google Sign-In with a new brand:

            $ {command} --app=1:123:web:abc --display-name="My App" --support-email=support@example.com

          To enable Google Sign-In with an existing OAuth client:

            $ {command} --app=1:123:web:abc --client-id=CLIENT_ID --client-secret=CLIENT_SECRET
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--app',
        required=True,
        help='The Firebase App ID to use.',
    )
    auth_config_group = parser.add_group(
        mutex=True,
        required=True,
        help='OAuth configuration for Google Sign-In.',
    )
    brand_group = auth_config_group.add_group(
        help='Brand configuration (for creating a new brand):'
    )
    brand_group.add_argument(
        '--display-name',
        required=True,
        help=(
            'The public display name for the OAuth brand (Google provider'
            ' only).'
        ),
    )
    brand_group.add_argument(
        '--support-email',
        required=True,
        help=(
            'The customer support email for the OAuth brand (Google provider'
            ' only).'
        ),
    )
    client_group = auth_config_group.add_group(
        help='Client configuration (for using an existing OAuth client):'
    )
    client_group.add_argument(
        '--client-id',
        required=True,
        help=(
            'The OAuth client ID (Google provider only, for existing client).'
        ),
    )
    client_group.add_argument(
        '--client-secret',
        required=True,
        help=(
            'The OAuth client secret (Google provider only, for existing'
            ' client).'
        ),
    )
    parser.add_argument(
        '--redirect-uris',
        type=arg_parsers.ArgList(),
        metavar='URI',
        help='Authorized redirect URIs (Google provider only).',
    )

  def Run(self, args):
    project_id = properties.VALUES.core.project.Get(required=True)

    log.status.Print(f'Enabling Google Sign-In for app {args.app}...')
    client = auth_util.AuthClient(release_track=self.ReleaseTrack())
    op = client.EnableGoogleSignIn(
        project_id=project_id,
        app_id=args.app,
        display_name=args.display_name,
        support_email=args.support_email,
        client_id=args.client_id,
        client_secret=args.client_secret,
        redirect_uris=args.redirect_uris,
    )
    poller = auth_util.FirebaseAuthOperationPoller(
        client.client, client.messages
    )
    wait_message = f'Waiting for operation [{op.name}] to complete...'
    result = waiter.WaitFor(poller, op.name, wait_message)
    log.status.Print('Successfully enabled Google Sign-In')
    return result

