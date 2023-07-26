# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Deploys a function locally."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.local import flags as local_flags
from googlecloudsdk.command_lib.functions.local import util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

_LOCAL_DEPLOY_MESSAGE = textwrap.dedent("""\
    Your function {name} is serving at localhost:{port}.

    To call this locally deployed function using gcloud:
    gcloud alpha functions local call {name} [--data=DATA] | [--cloud-event=CLOUD_EVENT]

    To call local HTTP functions using curl:
    curl -m 60 -X POST localhost:{port} -H "Content-Type: application/json" -d '{{}}'

    To call local CloudEvent and Background functions using curl, please see:
    https://cloud.google.com/functions/docs/running/calling
    """)
_RUNTIMES = ['python', 'go', 'java', 'nodejs', 'php', 'ruby', 'dotnet']
_APPENGINE_BUILDER = 'gcr.io/gae-runtimes/buildpacks/google-gae-22/{}/builder'
_DETAILED_HELP = {
    'DESCRIPTION': """
        `{command}` Deploy a Google Cloud Function locally.
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Deploy(base.Command):
  """Deploy a Google Cloud Function locally."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    local_flags.AddDeploymentNameFlag(parser)
    local_flags.AddPortFlag(parser)
    local_flags.AddBuilderFlag(parser)
    flags.AddEntryPointFlag(parser)
    flags.AddRuntimeFlag(parser, _RUNTIMES)
    # TODO(b/289323441): Add docker labels for flags.

    # TODO(b/287273158): Add logic to handle these flags.
    # flags.AddIgnoreFileFlag(parser)
    # Set track to GA to only add memory flag.
    # flags.AddFunctionMemoryAndCpuFlags(parser, base.ReleaseTrack.GA)
    # flags.AddSourceFlag(parser)
    # flags.AddFunctionTimeoutFlag(parser)
    # env_vars_util.AddUpdateEnvVarsFlags(parser)
    # env_vars_util.AddBuildEnvVarsFlags(parser)
    # TODO(b/287273158): Add flags: build-env-vars-file, env-vars-file

  def Run(self, args):
    util.ValidateDependencies()
    args = self.ValidateArgs(args)

    pack_args = self.BuildPackArgs(args)
    util.RunPack(pack_args)

    name = args.NAME[0]
    port = args.port
    util.RunDockerContainer(name, port)

    log.status.Print(_LOCAL_DEPLOY_MESSAGE.format(name=name, port=port))

  def BuildPackArgs(self, args):
    name = args.NAME[0]
    pack_args = ['build', '--builder']
    if args.builder:
      pack_args.append(args.builder)
    else:
      # Always use language-specific builder when builder not provided.
      pack_args.append(_APPENGINE_BUILDER.format(args.runtime))
    pack_args.extend(['--env', 'GOOGLE_FUNCTION_TARGET=' + args.entry_point])
    pack_args.extend(['-q', name])
    return pack_args

  def ValidateArgs(self, args):
    if not args.entry_point:
      raise calliope_exceptions.RequiredArgumentException(
          '--entry-point', 'Flag `--entry-point` required.'
      )
    # Require runtime if builder not specified.
    if not args.builder and not args.runtime:
      if not console_io.CanPrompt():
        raise calliope_exceptions.RequiredArgumentException(
            '--runtime', 'Flag `--runtime` required when builder not specified.'
        )
      idx = console_io.PromptChoice(
          _RUNTIMES, message='Please select a runtime:\n'
      )
      args.runtime = _RUNTIMES[idx]
    return args
