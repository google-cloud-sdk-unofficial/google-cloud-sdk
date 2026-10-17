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
"""Command to update an agent runtime in Vertex AI."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai.agent_runtimes import agent_runtimes_util
from googlecloudsdk.command_lib.ai.agent_runtimes import flags


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class Update(base.UpdateCommand):
  """Update an existing agent runtime.

  ## EXAMPLES

  To update the display name and memory limit of an existing agent runtime,
  run:

    $ {command} 123456789 --region=us-central1 --display-name="Updated name"
    --memory-limit=8Gi

  To deploy a new container image to an existing agent runtime, run:

    $ {command} 123456789 --region=us-central1
    --image=us-docker.pkg.dev/example/my-agent:v2
  """

  @staticmethod
  def Args(parser):
    flags.AddUpdateFlags(parser)

  def Run(self, args):
    runtime_ref = args.CONCEPTS.runtime.Parse()
    return agent_runtimes_util.UpdateRuntime(
        runtime_ref, args, self.ReleaseTrack(), asynchronous=False
    )
