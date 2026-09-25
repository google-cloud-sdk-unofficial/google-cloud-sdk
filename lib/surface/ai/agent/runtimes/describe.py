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
"""Command to describe an agent runtime in Vertex AI."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.ai.agent_runtimes import client
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UniverseCompatible
class Describe(base.DescribeCommand):
  """Get detailed information about an agent runtime with a given id.

  ## EXAMPLES

  To describe the agent runtime with id ``123'' under project ``example'' in
  region
  ``us-central1'', run:

    $ {command} 123 --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddAgentRuntimeResourceArg(parser, 'to describe')

  def Run(self, args):
    runtime_ref = args.CONCEPTS.runtime.Parse()
    region = runtime_ref.AsDict()['locationsId']
    if properties.IsDefaultUniverse():
      validation.ValidateRegion(
          region, available_regions=constants.SUPPORTED_AP_REGIONS
      )
    with endpoint_util.AiplatformEndpointOverrides(
        constants.BETA_VERSION, region=region
    ):
      try:
        return client.AgentRuntimesClient(version=constants.BETA_VERSION).Get(
            runtime_ref.RelativeName()
        )
      except apitools_exceptions.HttpError as error:
        # Translates generic HTTP error into a user-friendly gcloud exception
        raise api_exceptions.HttpException(
            error,
            'ResponseError: code={status_code}, message={status_message}',
        )
