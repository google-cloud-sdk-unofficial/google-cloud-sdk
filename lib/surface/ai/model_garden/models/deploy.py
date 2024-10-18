# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Model Garden deploy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.ai import operations
from googlecloudsdk.api_lib.ai.endpoints import client as client_endpoints
from googlecloudsdk.api_lib.ai.model_garden import client as client_mg
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import model_garden_utils
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Deploy(base.Command):
  """Deploy a model in Model Garden to a Vertex AI endpoint.

  ## EXAMPLES

  To deploy a Model Garden model `google/gemma2/gemma2-9b` under project
  `example` in region
  `us-central1`, run:

    $ gcloud ai model-garden models deploy
    --model=google/gemma2/gemma2-9b
    --project=example
    --region=us-central1

  To deploy a Hugging Face model `meta-llama/Meta-Llama-3-8B` under project
  `example` in region `us-central1`, run:

    $ gcloud ai model-garden models deploy
    --hugging-face-model=meta-llama/Meta-Llama-3-8B
    --hugging-face-access-token={hf_token}
    --project=example
    --region=us-central1
  """

  @staticmethod
  def Args(parser):
    model_group = parser.add_group(mutex=True, required=True)
    model_group.add_argument(
        '--model',
        help=(
            'The Model Garden model to be deployed, in the format of'
            ' `{publisher_name}/{model_name}/{model_version_name}, e.g.'
            ' `google/gemma2/gemma2-2b`.'
        ),
    )
    hf_model_group = model_group.add_group()
    hf_model_group.add_argument(
        '--hugging-face-model',
        required=True,
        help=(
            'The Hugging Face model to be deployed, in the format of Hugging'
            ' Face URL path, e.g. `meta-llama/Meta-Llama-3-8B`.'
        ),
    )
    hf_model_group.add_argument(
        '--hugging-face-access-token',
        help=(
            'The access token from Hugging Face needed to read the'
            ' model artifacts of gated models. It is only needed when'
            ' the model to deploy is gated.'
        ),
    )
    flags.GetDisplayNameArg('deployed endpoint', required=False).AddToParser(
        parser
    )
    flags.AddRegionResourceArg(
        parser, 'to deploy the model', prompt_func=region_util.PromptForOpRegion
    )
    base.Argument(
        '--machine-type',
        help=(
            'The machine type to deploy the model to. It should be a supported'
            ' machine type from the deployment configurations of the model. Use'
            ' `gcloud ai model-garden models list-deployment-config` to check'
            ' the supported machine types.'
        ),
        required=False,
    ).AddToParser(parser)

  def Run(self, args):
    validation.ValidateModelGardenModelArgs(args)
    validation.ValidateDisplayName(args.display_name)
    region_ref = args.CONCEPTS.region.Parse()
    args.region = region_ref.AsDict()['locationsId']
    is_hf_model = args.hugging_face_model is not None
    requires_hf_token = is_hf_model
    version = constants.BETA_VERSION

    # Step 1: Fetch PublisherModel data, including deployment configs. Use
    # us-central1 because all data are stored in us-central1.
    with endpoint_util.AiplatformEndpointOverrides(
        version, region='us-central1'
    ):
      mg_client = client_mg.ModelGardenClient(version)
      if is_hf_model:
        # Convert to lower case because API only takes in lower case.
        publisher_name, model_name = args.hugging_face_model.lower().split('/')

        try:
          publisher_model = mg_client.GetPublisherModel(
              model_name=f'publishers/{publisher_name}/models/{model_name}',
              is_hugging_face_model=True,
          )
        except apitools_exceptions.HttpUnauthorizedError:
          raise c_exceptions.UnknownArgumentException(
              '--hugging-face-model',
              f'{args.hugging_face_model} is not a supported Hugging Face model'
              ' for deployment in Model Garden.',
          )
        # Only requires HF access token in argument when the model is gated.
        requires_hf_token = model_garden_utils.IsHFModelGated(
            publisher_name, model_name
        )
        if requires_hf_token:
          if args.hugging_face_access_token is None:
            raise c_exceptions.RequiredArgumentException(
                '--hugging-face-access-token',
                '--hugging-face-access-token is required to read the model'
                ' artifacts of the gated Hugging Face model:'
                f' {args.hugging_face_model}.',
            )
          model_garden_utils.VerifyHFTokenPermission(
              args.hugging_face_access_token, publisher_name, model_name
          )

        default_endpoint_name = '-'.join(
            [publisher_name, model_name, 'hf', 'mg-cli-deploy']
        )
        endpoint_label_value = model_garden_utils.GetCLIEndpointLabelValue(
            is_hf_model, publisher_name, model_name=model_name
        )
      else:
        # Convert to lower case because API only takes in lower case.
        publisher_name, model_name, model_version_name = (
            args.model.lower().split('/')
        )
        publisher_model = mg_client.GetPublisherModel(
            f'publishers/{publisher_name}/models/{model_name}@{model_version_name}'
        )
        default_endpoint_name = '-'.join(
            [publisher_name, model_version_name, 'mg-cli-deploy']
        )
        endpoint_label_value = model_garden_utils.GetCLIEndpointLabelValue(
            is_hf_model, publisher_name, model_version_name=model_version_name
        )

      deploy_config = model_garden_utils.GetDeployConfig(args, publisher_model)
      model_garden_utils.CheckAcceleratorQuota(
          args,
          machine_type=deploy_config.dedicatedResources.machineSpec.machineType,
          accelerator_type=str(
              deploy_config.dedicatedResources.machineSpec.acceleratorType
          ),
          accelerator_count=deploy_config.dedicatedResources.machineSpec.acceleratorCount,
      )
      # Clear the aiplatform URI value so that new values can be set.
      properties.VALUES.api_endpoint_overrides.aiplatform.Set(None)

    with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
      operation_client = operations.OperationsClient(version=version)
      endpoints_client = client_endpoints.EndpointsClient(version=version)
      endpoint_name = (
          args.display_name if args.display_name else default_endpoint_name
      )
      # Step 2: Create a Vertex Endpoint.
      endpoint_id = model_garden_utils.CreateEndpoint(
          endpoint_name,
          endpoint_label_value,
          region_ref,
          operation_client,
          endpoints_client,
      )

      # Step 3: Upload the model to Model Registry.
      model_id = model_garden_utils.UploadModel(
          deploy_config,
          args,
          requires_hf_token,
          is_hf_model,
          endpoint_name,
          publisher_name,
          model_name,
      )

      # Step 4: Deploy the model from Model Registry to the Endpoint.
      model_garden_utils.DeployModel(
          args,
          deploy_config,
          endpoint_id,
          endpoint_name,
          model_id,
          endpoints_client,
          operation_client,
      )
      return
