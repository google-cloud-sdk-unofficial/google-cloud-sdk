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
"""Command to adjust traffic assignments for an agent runtime in Vertex AI."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai.agent_runtimes import agent_runtimes_util
from googlecloudsdk.command_lib.ai.agent_runtimes import flags


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UniverseCompatible
@base.RegionalEndpointsSupported
class UpdateTraffic(base.UpdateCommand):
  """Adjust traffic assignments for an agent runtime.

  ## EXAMPLES

  To route 100% of traffic to the latest runtime revision, run:

    $ {command} 123456789 --region=us-central1 --always-latest

  To assign 60% of traffic to revision `rev1` and 40% to revision `rev2`, run:

    $ {command} 123456789 --region=us-central1 --to-revisions=rev1=60,rev2=40
  """

  @staticmethod
  def Args(parser):
    flags.AddUpdateTrafficFlags(parser)

  def Run(self, args):
    runtime_ref = args.CONCEPTS.runtime.Parse()
    return agent_runtimes_util.UpdateTraffic(
        runtime_ref,
        args,
        asynchronous=args.async_,
    )
