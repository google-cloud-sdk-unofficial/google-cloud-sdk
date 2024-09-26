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
"""The command lists the deployment configurations of a given model supported by Model Garden."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.model_garden import client as client_mg
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.core import exceptions as core_exceptions


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class ListDeployMentConfig(base.Command):
  """List the deployment configurations supported by a model in Model Garden.

  ## EXAMPLES

  To list the deployment configurations for `google/gemma2/gemma2-9b`, run:

    $ gcloud ai model-garden models list-deployment-config
    --model=google/gemma2/gemma2-9b

  To list the deployment configurations for a Hugging Face model
  `meta-llama/Meta-Llama-3-8B`, run:

    $ gcloud ai model-garden models list-deployment-config
    --hugging-face-model=meta-llama/Meta-Llama-3-8B
  """

  def _GetMultiDeploy(self, args, version):
    mg_client = client_mg.ModelGardenClient(version)
    is_hf_model = args.hugging_face_model is not None
    if is_hf_model:
      # Convert to lower case because API only takes in lower case.
      publisher_name, model_name = args.hugging_face_model.lower().split('/')
      publisher_model = mg_client.GetPublisherModel(
          model_name=f'publishers/{publisher_name}/models/{model_name}',
          is_hugging_face_model=True,
      )
    else:
      # Convert to lower case because API only takes in lower case.
      publisher_name, model_name, model_version_name = args.model.lower().split(
          '/'
      )
      publisher_model = mg_client.GetPublisherModel(
          f'publishers/{publisher_name}/models/{model_name}@{model_version_name}'
      )

    try:
      multi_deploy = (
          publisher_model.supportedActions.multiDeployVertex.multiDeployVertex
      )
    except AttributeError:
      raise core_exceptions.Error(
          'Model does not support deployment, please use a deploy-able model'
          ' instead. You can use the `gcloud ai model-garden models list`'
          ' command to find out which ones are currently supported by the'
          ' `deploy` command.'
      )
    return multi_deploy

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
    model_group.add_argument(
        '--hugging-face-model',
        help=(
            'The Hugging Face model to be deployed, in the format of Hugging'
            ' Face URL path, e.g. `meta-llama/Meta-Llama-3-8B`.'
        ),
    )

  def Run(self, args):
    validation.ValidateModelGardenModelArgs(args)
    version = constants.BETA_VERSION

    # Use us-central1 because all data are stored in us-central1.
    with endpoint_util.AiplatformEndpointOverrides(
        version, region='us-central1'
    ):
      return list(
          deploy_config.dedicatedResources.machineSpec
          for deploy_config in self._GetMultiDeploy(args, version)
      )
