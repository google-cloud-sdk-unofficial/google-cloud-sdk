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

"""Vertex AI endpoints mutate-deployed-model command."""

from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import endpoints_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import operations_util
from googlecloudsdk.core import log


def _AddArgs(parser):
  flags.AddMutateDeployedModelArgs(parser)


def _Run(args):
  """Mutate a deployed model."""
  endpoint_ref = args.CONCEPTS.endpoint.Parse()
  args.region = endpoint_ref.AsDict()['locationsId']

  version = constants.BETA_VERSION
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    endpoints_client = client.EndpointsClient(version=version)
    operation_client = operations.OperationsClient()

    op = endpoints_client.MutateDeployedModelBeta(
        endpoint_ref=endpoint_ref,
        deployed_model_id=args.deployed_model_id,
        min_replica_count=args.min_replica_count,
        max_replica_count=args.max_replica_count,
    )

    response_msg = operations_util.WaitForOpMaybe(
        operation_client, op, endpoints_util.ParseOperation(op.name))
    log.status.Print('Mutated deployed model [{}] on endpoint [{}].'.format(
        args.deployed_model_id, endpoint_ref.AsDict()['endpointsId']))
    return response_msg


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
@base.Hidden
@base.UniverseCompatible
class MutateDeployedModel(base.Command):
  r"""Mutate a deployed model in a Vertex AI endpoint.

  ## EXAMPLES

  To mutate a deployed model ``456'' in an endpoint ``123'' under project
  ``example'' in region ``us-central1'' to have min replica count 2 and max
  replica count 5, run:

    $ {command} 123 --project=example --region=us-central1 \
        --deployed-model-id=456 \
        --min-replica-count=2 \
        --max-replica-count=5
  """

  @staticmethod
  def Args(parser):
    _AddArgs(parser)

  def Run(self, args):
    return _Run(args)
