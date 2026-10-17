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
"""Flag definitions for the `gcloud ai agent runtimes` commands.

The `create`, `update` and `deploy` commands share almost their entire flag
surface, so every flag is declared once here and assembled into a command's
parser by the `Add*Flags` entry points at the bottom of this module.
"""

from __future__ import annotations

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import flags as shared_flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.util.args import labels_util


# Choices for `--agent-server-mode`, mapped to the API enum in
# agent_runtimes_util.AgentRuntimeBuilder.
AGENT_SERVER_MODES = ('stable', 'experimental')


def _AddSourceFlags(parser, required=False):
  """Adds the flags describing where the agent's code comes from.

  Args:
    parser: the parser for the command.
    required: bool, whether a source must be provided.
  """
  if required:
    group_help = "Argument group for agent's source."
  else:
    group_help = (
        "Argument group for agent's source. If none of the flags from this"
        ' group are provided, the runtime is created or updated without'
        ' triggering a deployment.'
    )
  source_group = parser.add_group(
      mutex=True,
      required=required,
      help=group_help,
  )
  source_group.add_argument(
      '--image',
      help=(
          'Artifact Registry URI of the container image to use for the agent'
          ' runtime.'
      ),
  )

  source_subgroup = source_group.add_group(
      help=(
          'Shared arguments for source based deployment or Bring Your Own'
          ' Dockerfile.'
      )
  )
  source_subgroup.add_argument(
      '--source',
      required=True,
      help='Path to the source code directory.',
  )

  source_type_group = source_subgroup.add_group(
      mutex=True,
      help='Deployment type arguments for source-based deployment.',
  )
  source_type_group.add_argument(
      '--build-args',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help='Custom container build arguments passed during image compilation.',
  )

  python_group = source_type_group.add_group(
      help='Exclusive arguments for source based deployment.'
  )
  python_group.add_argument(
      '--entrypoint-module',
      help=(
          'Fully qualified Python module name to load as the application'
          ' entrypoint.'
      ),
  )
  python_group.add_argument(
      '--entrypoint-object',
      help='Name of the callable agent object within the entrypoint module.',
  )
  python_group.add_argument(
      '--requirements-file',
      help=(
          'Path to the dependency requirements file relative to the source'
          ' root.'
      ),
  )
  python_group.add_argument(
      '--python-version',
      help='Python runtime version for source deployment.',
  )


def _AddIdentityFlags(parser):
  """Adds the flags selecting the identity the agent runtime runs as."""
  identity_group = parser.add_group(
      mutex=True,
      help="Argument group for agent's identity.",
  )
  identity_group.add_argument(
      '--default-service-account',
      action='store_true',
      default=None,
      help='Use the default service agent for the agent runtime.',
  )
  identity_group.add_argument(
      '--service-account',
      help='IAM service account email under which the agent runtime executes.',
  )
  identity_group.add_argument(
      '--use-agent-identity',
      action='store_true',
      default=None,
      help='Use the agent identity for the agent runtime.',
  )


def _AddAgentDefinitionFlags(parser, display_name_required=False):
  """Adds the flags describing the agent itself."""
  parser.add_argument(
      '--display-name',
      required=display_name_required,
      help='Human-readable display name of the agent runtime.',
  )
  parser.add_argument(
      '--description',
      help='Description of the agent runtime.',
  )
  parser.add_argument(
      '--agent-framework',
      help=(
          'Underlying agent framework (e.g., google-adk, langchain,'
          ' langgraph).'
      ),
  )
  parser.add_argument(
      '--agent-card-file',
      help=(
          'Path to a JSON/YAML file defining the A2A Agent Card specification.'
      ),
  )
  parser.add_argument(
      '--class-methods-file',
      help=(
          'Path to a JSON/YAML file declaring object class methods in OpenAPI'
          ' specification format. For details, see'
          ' https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/runtime-contract#class-methods'
      ),
  )


def _AddDeploymentFlags(parser):
  """Adds the flags configuring how the agent is served."""
  parser.add_argument(
      '--env-vars',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help='List of key-value pairs to set as environment variables.',
  )
  parser.add_argument(
      '--secret-env-vars',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=(
          'List of key-value pairs to set as secret environment variables'
          ' (VAR=SECRET:VERSION).'
      ),
  )
  parser.add_argument(
      '--min-instances',
      type=arg_parsers.BoundedInt(0, 75),
      help=(
          'Minimum number of application container instances kept running'
          ' continuously.'
      ),
  )
  parser.add_argument(
      '--max-instances',
      type=arg_parsers.BoundedInt(1, 1000),
      help=(
          'Maximum number of application container instances scaled to handle'
          ' traffic spikes.'
      ),
  )
  parser.add_argument(
      '--cpu-limit',
      help=(
          'CPU core allocation limit for each container instance (e.g., 2, 4).'
      ),
  )
  parser.add_argument(
      '--memory-limit',
      help=(
          'Memory allocation limit for each container instance (e.g., 4Gi,'
          ' 8Gi).'
      ),
  )
  parser.add_argument(
      '--container-concurrency',
      type=arg_parsers.BoundedInt(1),
      help=(
          'Maximum number of concurrent requests processed per container'
          ' instance.'
      ),
  )
  parser.add_argument(
      '--agent-server-mode',
      choices=AGENT_SERVER_MODES,
      help='Feature release channel mode for the agent server runtime.',
  )
  parser.add_argument(
      '--network-attachment',
      help=(
          'Compute Engine network attachment resource name for PSC-I'
          ' connectivity.'
      ),
  )
  parser.add_argument(
      '--dns-peering-configs',
      action='append',
      metavar='DOMAIN=DOMAIN,TARGET_PROJECT=PROJECT,TARGET_NETWORK=NETWORK',
      type=arg_parsers.ArgDict(
          spec={
              'domain': str,
              'target-project': str,
              'target-network': str,
          },
          required_keys=['domain', 'target-project', 'target-network'],
      ),
      help=(
          'DNS peering configuration for resolving private internal zones via'
          ' Cloud DNS.'
      ),
  )
  parser.add_argument(
      '--client-to-agent-gateway',
      help=(
          'Agent Gateway resource name governing inbound client-to-agent'
          ' traffic.'
      ),
  )
  parser.add_argument(
      '--agent-to-anywhere-gateway',
      help=(
          'Agent Gateway resource name governing outbound agent-to-anywhere'
          ' traffic.'
      ),
  )
  parser.add_argument(
      '--keep-alive-probe-path',
      help=(
          'HTTP GET endpoint path invoked by the platform to keep the container'
          ' alive.'
      ),
  )
  parser.add_argument(
      '--keep-alive-probe-port',
      type=int,
      help='Container port number targeted by keep-alive HTTP probe requests.',
  )
  parser.add_argument(
      '--keep-alive-probe-timeout',
      metavar='DURATION',
      type=arg_parsers.Duration(lower_bound='900s', upper_bound='3600s'),
      help=(
          'Maximum duration to keep the instance alive following a probe,'
          ' between 15m and 1h.'
      ),
  )


def AddCreateFlags(parser):
  """Adds all the flags of `gcloud ai agent runtimes create`."""
  shared_flags.AddRegionResourceArg(
      parser,
      'to create an agent runtime in',
      prompt_func=region_util.PromptForOpRegion,
  )
  base.ASYNC_FLAG.AddToParser(parser)
  _AddSourceFlags(parser)
  _AddIdentityFlags(parser)
  _AddAgentDefinitionFlags(parser, display_name_required=True)
  labels_util.AddCreateLabelsFlags(parser)
  parser.add_argument(
      '--kms-key-name',
      help='Cloud KMS customer-managed encryption key (CMEK) resource name.',
  )
  _AddDeploymentFlags(parser)
