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
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.auth import auth_util
from googlecloudsdk.command_lib.transfer import creds_util
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import platforms

from oauth2client import client as oauth2_client

_AUTH_PROXY_REDIRECT_URI = (
    'https://sdk.cloud.google.com/transfer-agents-install-authcode.html')
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
MOUNT_DIRECTORIES_HELP_TEXT = """
If you want to grant agents access to specific parts of your filesystem
instead of the entire filesystem, specify which directory paths to
mount to the agent container. Multiple paths must be separated by
commas with no spaces (e.g.,
--mount-directories=/system/path/to/dir1,/path/to/dir2). When mounting
specific directories, gcloud transfer will also mount a directory for
logs (either /tmp or what you've specified for --logs-directory) and
your Google credentials file for agent authentication.

It is strongly recommended that you use this flag. If this flag isn't specified,
gcloud transfer will mount your entire filesystem to the agent container and
give the agent root access.
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

If your agent does not appear in the pool, check its local logs by running
"docker container logs [container ID]". The container ID is the string of random
characters printed by step [2/3]. The container ID can also be found by running
"docker container list".
"""

S3_COMPATIBLE_HELP_TEXT = """
Allow the agent to work with S3-compatible sources. This flag blocks the
agent's ability to work with other source types (e.g., file systems).

When using this flag, you must provide source credentials either as
environment variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` or
as default credentials in your system's configuration files.

To provide credentials as environment variables, run:

```
AWS_ACCESS_KEY_ID="id" AWS_SECRET_ACCESS_KEY="secret" gcloud transfer agents install --s3-compatible-mode
```
"""


def _expand_path(path):
  """Converts relative and symbolic paths to absolute paths."""
  return os.path.abspath(os.path.expanduser(path))


def _authenticate_and_get_creds_file_path(existing_creds_file=None):
  """Ensures agent will be able to authenticate and returns creds."""
  # Can't disable near "else" (https://github.com/PyCQA/pylint/issues/872).
  # pylint:disable=protected-access
  if existing_creds_file:
    creds_file_path = _expand_path(existing_creds_file)
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
          scopes=(login_util.DEFAULT_SCOPES + [config.REAUTH_SCOPE]),
          auth_proxy_redirect_uri=_AUTH_PROXY_REDIRECT_URI,
      )
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


def _get_docker_command(args, project, creds_file_path):
  """Returns docker command from user arguments and generated values."""
  base_docker_command = [
      'docker',
      'run',
      '--ulimit',
      'memlock={}'.format(args.memlock_limit),
      '--rm',
      '-d',
  ]
  aws_access_key, aws_secret_key = creds_util.get_default_aws_creds()
  if aws_access_key:
    base_docker_command.append('--env')
    base_docker_command.append('AWS_ACCESS_KEY_ID={}'.format(aws_access_key))
  if aws_secret_key:
    base_docker_command.append('--env')
    base_docker_command.append(
        'AWS_SECRET_ACCESS_KEY={}'.format(aws_secret_key))

  expanded_creds_file_path = _expand_path(creds_file_path)
  expanded_logs_directory_path = _expand_path(args.logs_directory)
  if args.mount_directories:
    # Mount mandatory directories.
    mount_flags = [
        '-v={}:/tmp'.format(expanded_logs_directory_path),
        '-v={creds_file_path}:{creds_file_path}'.format(
            creds_file_path=expanded_creds_file_path),
    ]
    for path in args.mount_directories:
      if path == '/':
        # Docker can't handle mounting to root.
        mount_flags.append('-v=/:/transfer_root')
      else:
        # Mount custom directory.
        mount_flags.append('-v={path}:{path}'.format(path=path))
    base_docker_command.extend(mount_flags)
  else:
    # Mount entire filesystem by default.
    base_docker_command.append('-v=/:/transfer_root')

  if args.proxy:
    base_docker_command.append('--env')
    base_docker_command.append('HTTPS_PROXY={}'.format(args.proxy))

  agent_args = [
      'gcr.io/cloud-ingest/tsop-agent:latest',
      '--agent-pool={}'.format(args.pool),
      '--creds-file={}'.format(expanded_creds_file_path),
      '--hostname={}'.format(socket.gethostname()),
      '--log-dir={}'.format(expanded_logs_directory_path),
      '--project-id={}'.format(project),
  ]
  if args.enable_multipart:
    agent_args.append('--enable-multipart')
  if not args.mount_directories:
    # Needed to mount entire filesystem.
    agent_args.append('--enable-mount-directory')
  if args.id_prefix:
    if args.count is not None:
      agent_id_prefix = args.id_prefix + '0'
    else:
      agent_id_prefix = args.id_prefix
    # ID prefix must be the last argument for multipe-agent creation to work.
    agent_args.append('--agent-id-prefix={}'.format(agent_id_prefix))
  if args.s3_compatible_mode:
    # TODO(b/238213039): Remove when this flag becomes optional.
    agent_args.append('--enable-s3')
  return base_docker_command + agent_args


def _execute_and_return_docker_command(args, project, creds_file_path):
  """Generates, executes, and returns agent install and run command."""
  full_docker_command = _get_docker_command(args, project, creds_file_path)

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
    parser.add_argument(
        '--pool',
        required=True,
        help='The agent pool to associate with the newly installed agent.'
        ' When creating transfer jobs, the agent pool parameter will determine'
        ' which agents are activated.')
    parser.add_argument('--count', type=int, help=COUNT_FLAG_HELP_TEXT)
    parser.add_argument('--creds-file', help=CREDS_FILE_FLAG_HELP_TEXT)
    parser.add_argument(
        '--enable-multipart',
        action='store_true',
        help='Split up files and transfer the resulting chunks in parallel'
        ' before merging them at the destination. Can be used make transfers of'
        ' large files faster as long as the network and disk speed are not'
        ' limiting factors.')
    parser.add_argument(
        '--id-prefix',
        help='An optional prefix to add to the agent ID to help identify the'
        ' agent.')
    parser.add_argument(
        '--logs-directory',
        default='/tmp',
        help='Specify the absolute path to the directory you want to store'
        ' transfer logs in. If not specified, gcloud transfer will mount your'
        ' /tmp directory for logs.')
    parser.add_argument(
        '--memlock-limit',
        default=64000000,
        type=int,
        help="Set the agent container's memlock limit. A value of 64000000"
        ' (default) or higher is required to ensure that agent versions'
        ' 1.14 or later have enough locked memory to be able to start.')
    parser.add_argument(
        '--mount-directories',
        type=arg_parsers.ArgList(),
        metavar='MOUNT-DIRECTORIES',
        help=MOUNT_DIRECTORIES_HELP_TEXT)
    parser.add_argument('--proxy', help=PROXY_FLAG_HELP_TEXT)
    parser.add_argument(
        '--s3-compatible-mode',
        action='store_true',
        help=S3_COMPATIBLE_HELP_TEXT)

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
