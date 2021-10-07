# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to install on-premise Transfer agent."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import shutil
import sys

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import config
from googlecloudsdk.core import log

from oauth2client import client as oauth2_client

CREDS_FILE_FLAG_HELP_TEXT = """
Specify the path to the service account's credentials file.

No input required if authenticating with your user account credentials,
which Transfer Service will look for in your system.

Note that the credentials location will be mounted to the agent container.
"""

DOCKER_NOT_FOUND_HELP_TEXT_FORMAT = """
The agent runs inside a Docker container, so you'll need
to install Docker before finishing agent installation.

For most Linux operating systems, you can copy and run the piped installation
commands below:

curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh &&
sudo systemctl enable docker && gcloud {gcloud_args}

For other operating systems, see the installation instructions at
https://docs.docker.com/engine/install/binaries/ and re-run
'gcloud {gcloud_args}' after Docker installation.
"""


class Install(base.Command):
  """Installs an on-premise Transfer agent."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Install Transfer Service agents to enable the transfer of data from POSIX
      filesystem sources (for example, on-premises filesystems).
      """,
      'EXAMPLES':
          """\
      To install an agent that authenticates with your user account credentials
      and has default agent parameters, run:

        $ {command}

      To install an agent that authenticates with a service account with
      credentials stored at '/example/path.json', run:

        $ {command} --creds-file=/example/path.json

      """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('--creds-file', help=CREDS_FILE_FLAG_HELP_TEXT)

  def Run(self, args):
    if args.creds_file:
      creds_file_path = os.path.abspath(os.path.expanduser(args.creds_file))
      if not os.path.exists(creds_file_path):
        raise OSError(
            'Credentials file not found at {}. Check for typos and ensure a'
            ' creds file exists at the path, then re-run the command.'.format(
                creds_file_path))
    else:
      # pylint:disable=protected-access
      creds_file_path = oauth2_client._get_well_known_file()
      # pylint:enable=protected-access
      if not os.path.exists(creds_file_path):
        auth_util.DoInstalledAppBrowserFlowGoogleAuth(
            launch_browser=False,
            scopes=(auth_util.DEFAULT_SCOPES + [config.REAUTH_SCOPE]))

      # TODO(b/201418852): Unused until Docker call is implemented.
      del creds_file_path

    log.status.Print('[1/3] Credentials found ✓')

    if not shutil.which('docker'):
      log.error('[2/3] Docker not found')
      raise OSError(
          DOCKER_NOT_FOUND_HELP_TEXT_FORMAT.format(
              gcloud_args=' '.join(sys.argv[1:])))

    log.status.Print('[2/3] Docker found ✓')
    raise NotImplementedError
