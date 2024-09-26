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
"""Model Garden endpoints list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import model_garden_utils
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.core import resources

_DEFAULT_FORMAT = """
        table(
            name.basename():label=ENDPOINT_ID,
            displayName,
            deployedModels.yesno(yes=Yes):label=HAS_DEPLOYED_MODEL,
            deployedModels[0].id:label=DEPLOYED_MODEL_ID
        )
    """


def _GetUri(endpoint):
  ref = resources.REGISTRY.ParseRelativeName(
      endpoint.name, constants.ENDPOINTS_COLLECTION
  )
  return ref.SelfLink()


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class List(base.ListCommand):
  """List existing Vertex AI endpoints.

  ## EXAMPLES

  To list the Model Garden endpoints under project ``example'' in region
  ``us-central1'',
  run:

    $ {command} --project=example --region=us-central1

  To list the endpoints for Model Garden models under project ``example'' in
  region
  ``us-central11'',
  run:
    $ {command} --model={publisher_name}/{model_name}/{model_version_name}
    --project=example --region=us-central1

  To list the endpoints for Hugging Face models under project ``example'' in
  region
  ``us-central11'',
  run:
    $ {command} --hugging-face-model={organization_name}/{model_name}
    --project=example --region=us-central1
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(_DEFAULT_FORMAT)
    parser.display_info.AddUriFunc(_GetUri)
    flags.AddRegionResourceArg(
        parser,
        'to list Model Garden endpoints',
        prompt_func=region_util.PromptForOpRegion,
    )
    model_group = parser.add_group(mutex=True)
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
    region_ref = args.CONCEPTS.region.Parse()
    args.region = region_ref.AsDict()['locationsId']
    list_all_models = args.model is None and args.hugging_face_model is None
    cli_label_filter, one_click_filter = '', ''
    if args.model is not None:
      cli_label_filter = model_garden_utils.GetCLIEndpointLabelValue(
          is_hf_model=False,
          publisher_name=args.model.lower().split('/')[0],
          model_version_name=args.model.lower().split('/')[2],
      )
      one_click_filter = model_garden_utils.GetOneClickEndpointLabelValue(
          is_hf_model=False,
          publisher_name=args.model.lower().split('/')[0],
          model_name=args.model.lower().split('/')[1],
          model_version_name=args.model.lower().split('/')[2],
      )
    elif args.hugging_face_model is not None:
      cli_label_filter = model_garden_utils.GetCLIEndpointLabelValue(
          is_hf_model=True,
          publisher_name=args.hugging_face_model.lower().split('/')[0],
          model_name=args.hugging_face_model.lower().split('/')[1],
      )
      one_click_filter = model_garden_utils.GetOneClickEndpointLabelValue(
          is_hf_model=True,
          publisher_name=args.hugging_face_model.lower().split('/')[0],
          model_name=args.hugging_face_model.lower().split('/')[1],
      )

    if list_all_models:
      cli_filter_str = 'labels.mg-cli-deploy:*'
      one_click_filter_str = 'labels.mg-one-click-deploy:*'
    else:
      cli_filter_str = f'labels.mg-cli-deploy={cli_label_filter}'
      if args.model is not None:
        one_click_filter_str = (
            f'labels.versioned-mg-one-click-deploy={one_click_filter}'
        )
      else:
        one_click_filter_str = f'labels.mg-one-click-deploy={one_click_filter}'

    with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
      cli_endpoints = client.EndpointsClient(version=version).List(
          region_ref, cli_filter_str + ' OR ' + one_click_filter_str
      )
      return cli_endpoints
