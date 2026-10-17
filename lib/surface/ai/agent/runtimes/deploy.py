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
"""Command to deploy an agent runtime in Vertex AI."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai.agent_runtimes import agent_runtimes_util
from googlecloudsdk.command_lib.ai.agent_runtimes import flags


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class Deploy(base.SilentCommand):
  """Create or update an Agent Runtime and trigger a deployment.

  If RUNTIME is provided, the existing runtime is updated; otherwise a new
  runtime is created.

  When creating a new runtime (RUNTIME is not provided), `--display-name` and
  either `--image` or `--source` are required. When
  updating an existing runtime (RUNTIME is provided), `--image` and `--source`
  are optional if updating other configuration settings.

  ## EXAMPLES

  To deploy a new agent runtime from a container image, run:

    $ {command} --display-name="My agent"
    --image=us-docker.pkg.dev/example/my-agent:latest --region=us-central1

  To deploy a new agent runtime from local source code, run:

    $ {command} --display-name="My agent" --source=./my-agent
    --entrypoint-module=my_agent.agent --region=us-central1

  To update an existing agent runtime with a new container image, run:

    $ {command} 123456789 --region=us-central1
    --image=us-docker.pkg.dev/example/my-agent:v2
  """

  @staticmethod
  def Args(parser):
    flags.AddDeployFlags(parser)

  def Run(self, args):
    runtime_ref = args.CONCEPTS.runtime.Parse()
    if runtime_ref is None:
      return self._Create(args)
    return self._Update(args, runtime_ref)

  def _Create(self, args):
    """Creates a new agent runtime."""
    region_ref = args.CONCEPTS.region.Parse()
    return agent_runtimes_util.CreateRuntime(
        region_ref,
        args,
        self.ReleaseTrack(),
        asynchronous=False,
        for_deploy=True,
    )

  def _Update(self, args, runtime_ref):
    """Updates an existing agent runtime."""
    return agent_runtimes_util.UpdateRuntime(
        runtime_ref,
        args,
        self.ReleaseTrack(),
        asynchronous=False,
        for_deploy=True,
    )

