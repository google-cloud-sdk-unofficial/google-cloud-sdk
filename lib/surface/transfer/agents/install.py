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
import socket
import subprocess
import sys

from googlecloudsdk.api_lib.auth import util as login_util
from googlecloudsdk.api_lib.transfer import agent_pools_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.auth import auth_util
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import platforms

from oauth2client import client as oauth2_client

COUNT_FLAG_HELP_TEXT = """
Specify the number of agents to install on your current machine.
System requirements: 8 GB of memory and 4 CPUs per agent.

Note: If the 'id-prefix' flag is specified, Transfer Service increments a number
value after each prefix. Example: prefix1, prefix2, etc.
"""
CREDS_FILE_FLAG_HELP_TEXT = """
Specify the path to the service account's credentials file.

No input required if authenticating with your user account credentials,
which Transfer Service will look for in your system.

Note that the credentials location will be mounted to the agent container.
"""
MISSING_PROJECT_ERROR_TEXT = """
Could not find project ID. Try adding the project flag: --project=[project-id]
"""
PROXY_FLAG_HELP_TEXT = """
Specify the HTTP URL and port of a proxy server if you want to use a forward
proxy. For example, to use the URL 'example.com' and port '8080' specify
'http://www.example.com:8080/'

Ensure that you specify the HTTP URL and not an HTTPS URL to avoid
double-wrapping requests in TLS encryption. Double-wrapped requests prevent the
proxy server from sending valid outbound requests.
"""

DOCKER_NOT_FOUND_HELP_TEXT_BASE_FORMAT = """
The agent runs inside a Docker container, so you'll need
to install Docker before finishing agent installation.

{os_instructions}
"""

DOCKER_NOT_FOUND_HELP_TEXT_LINUX_FORMAT = (
    DOCKER_NOT_FOUND_HELP_TEXT_BASE_FORMAT.format(os_instructions="""
For most Linux operating systems, you can copy and run the piped installation
commands below:

curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh &&
sudo systemctl enable docker && gcloud {gcloud_args}
"""))

DOCKER_NOT_FOUND_HELP_TEXT_NON_LINUX_FORMAT = (
    DOCKER_NOT_FOUND_HELP_TEXT_BASE_FORMAT.format(os_instructions="""
See the installation instructions at
https://docs.docker.com/engine/install/binaries/ and re-run
'gcloud {gcloud_args}' after Docker installation.
"""))

CHECK_AGENT_CONNECTED_HELP_TEXT_FORMAT = """
To confirm your agents are connected, go to the following link in your browser,
and check that agent status is 'Connected' (it can take a moment for the status
to update and may require a page refresh):

https://console.cloud.google.com/transfer/on-premises/agent-pools/pool/\
{pool}/agents?project={project}
"""


def _authenticate_and_get_creds_file_path(existing_creds_file=None):
  """Ensures agent will be able to authenticate and returns creds."""
  # Can't disable near "else" (https://github.com/PyCQA/pylint/issues/872).
  # pylint:disable=protected-access
  if existing_creds_file:
    creds_file_path = os.path.abspath(os.path.expanduser(existing_creds_file))
    if not os.path.exists(creds_file_path):
      raise OSError(
          'Credentials file not found at {}. Check for typos and ensure a'
          ' creds file exists at the path, then re-run the command.'.format(
              creds_file_path))
  else:
    creds_file_path = oauth2_client._get_well_known_file()
    # pylint:enable=protected-access
    if not os.path.exists(creds_file_path):
      creds = login_util.DoInstalledAppBrowserFlowGoogleAuth(
          launch_browser=False,
          scopes=(login_util.DEFAULT_SCOPES + [config.REAUTH_SCOPE]))
      auth_util.DumpADCOptionalQuotaProject(creds)

  return creds_file_path


def _check_if_docker_installed():
  """Checks for 'docker' in system PATH."""
  if not shutil.which('docker'):
    log.error('[2/3] Docker not found')
    if platforms.OperatingSystem.Current() == platforms.OperatingSystem.LINUX:
      error_format = DOCKER_NOT_FOUND_HELP_TEXT_LINUX_FORMAT
    else:
      error_format = DOCKER_NOT_FOUND_HELP_TEXT_NON_LINUX_FORMAT

    raise OSError(error_format.format(gcloud_args=' '.join(sys.argv[1:])))


def _execute_and_return_docker_command(args, project, creds_file_path):
  """Generates, executes, and returns agent install and run command."""
  base_docker_command = [
      'docker',
      'run',
      '--ulimit',
      'memlock={}'.format(args.memlock_limit),
      '--rm',
      '-d',
      '-v=/:/transfer_root',
  ]
  if args.proxy:
    base_docker_command.append('--env')
    base_docker_command.append('HTTPS_PROXY={}'.format(args.proxy))
  agent_args = [
      'gcr.io/cloud-ingest/tsop-agent:latest',
      '--enable-mount-directory',
      '--project-id={}'.format(project),
      '--creds-file={}'.format(creds_file_path),
      '--hostname={}'.format(socket.gethostname()),
      '--agent-pool={}'.format(args.pool),
  ]
  if args.id_prefix:
    if args.count is not None:
      agent_id_prefix = args.id_prefix + '0'
    else:
      agent_id_prefix = args.id_prefix
    # ID prefix must be the last argument for multipe-agent creation to work.
    agent_args.append('--agent-id-prefix={}'.format(agent_id_prefix))
  full_docker_command = base_docker_command + agent_args

  completed_process = subprocess.run(full_docker_command, check=False)
  if completed_process.returncode != 0:
    log.status.Print('\nCould not execute Docker command. Trying with "sudo".')
    sudo_full_docker_command = ['sudo'] + full_docker_command
    sudo_completed_process = subprocess.run(
        sudo_full_docker_command, check=False)
    if sudo_completed_process.returncode != 0:
      raise OSError('Error executing Docker command:\n{}'.format(
          ' '.join(full_docker_command)))
    return sudo_full_docker_command

  return full_docker_command


def _create_additional_agents(agent_count, agent_id_prefix, docker_command):
  """Creates multiple identical agents."""
  for i in range(1, agent_count):
    if agent_id_prefix:
      # docker_command is a list, so copy to avoid  mutating the original.
      # Agent ID prefix is always the last argument.
      docker_command_to_run = docker_command[:-1] + [
          '--agent-id-prefix={}{}'.format(agent_id_prefix, i)
      ]
    else:
      docker_command_to_run = docker_command

    # Less error handling than before. Just propogate any process errors.
    subprocess.run(docker_command_to_run, check=True)


class Install(base.Command):
  """Install Transfer Service agents."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Install Transfer Service agents to enable you to transfer data to or from
      POSIX filesystems, such as on-premises filesystems. Agents are installed
      locally on your machine and run inside Docker containers.
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
    parser.add_argument('--count', type=int, help=COUNT_FLAG_HELP_TEXT)
    parser.add_argument('--creds-file', help=CREDS_FILE_FLAG_HELP_TEXT)
    parser.add_argument(
        '--id-prefix',
        help='An optional prefix to add to the agent ID to help identify the'
        ' agent.')
    parser.add_argument(
        '--memlock-limit',
        default=64000000,
        type=int,
        help="Set the agent container's memlock limit. A value of 64000000"
        ' (default) or higher is required to ensure that agent versions'
        ' 1.14 or later have enough locked memory to be able to start.')
    parser.add_argument('--proxy', help=PROXY_FLAG_HELP_TEXT)
    parser.add_argument(
        '--pool',
        default='transfer_service_default',
        help='The agent pool associated with the filesystem for'
        ' which this agent will handle transfer work.')

  def Run(self, args):
    if args.count is not None and args.count < 1:
      raise ValueError('Agent count must be greater than zero.')

    project = properties.VALUES.core.project.Get()
    if not project:
      raise ValueError(MISSING_PROJECT_ERROR_TEXT)

    messages = apis.GetMessagesModule('storagetransfer', 'v1')
    if (agent_pools_util.api_get(args.pool).state !=
        messages.AgentPool.StateValueValuesEnum.CREATED):
      raise ValueError('Agent pool not found: ' + args.pool)

    creds_file_path = _authenticate_and_get_creds_file_path(args.creds_file)
    log.status.Print('[1/3] Credentials found ✓')

    _check_if_docker_installed()
    log.status.Print('[2/3] Docker found ✓')

    docker_command = _execute_and_return_docker_command(args, project,
                                                        creds_file_path)
    if args.count is not None:
      _create_additional_agents(args.count, args.id_prefix, docker_command)
    log.status.Print('[3/3] Agent installation complete! ✓')
    log.status.Print(
        CHECK_AGENT_CONNECTED_HELP_TEXT_FORMAT.format(
            pool=args.pool, project=project))
