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
"""The command lists the models in Model Garden and their supported functionalities."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.model_garden import client as client_mg
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util

_DEFAULT_FORMAT = """
        table(
            format("{0:s}@{1:s}/{2:s}", name, versionId, name.regex("publishers/hf-.*", "@hf", "@mg")).sub("publishers/hf-", "").sub("publishers/", "").sub("models/", "").sub("@001/@hf", ""). sub("/@mg", ""):sort=1:label=MODEL_ID,
            supportedActions.multiDeployVertex.if(NOT list_supported_hugging_face_models).yesno(yes=Yes):label=SUPPORTS_DEPLOYMENT
        )
    """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class List(base.ListCommand):
  """List the publisher models in Model Garden.

  This command lists either all models in Model Garden or all Hugging
  Face models supported by Model Garden.

  Note: Since the number of Hugging Face models is large, the default limit is
  set to 500 with a page size of 100 when listing supported Hugging Face models.
  To override the limit or page size, specify the --limit or --page-size flags,
  respectively. To list all models in Model Garden, use `--limit=unlimited`.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(_DEFAULT_FORMAT)
    parser.add_argument(
        '--list-supported-hugging-face-models',
        action='store_true',
        default=False,
        required=False,
        help='Whether to only list supported Hugging Face models.',
    )
    parser.add_argument(
        '--model-filter',
        action='store',
        default=None,
        required=False,
        help=(
            'Filter to apply to the model names or the display names of the'
            ' list of models.'
        ),
    )
    base.URI_FLAG.RemoveFromParser(parser)
    base.LIMIT_FLAG.SetDefault(parser, 1000)

  def Run(self, args):
    version = constants.BETA_VERSION
    # Set the default page size to 100 if the user requests to list supported
    # Hugging Face models, since there are tens of thousands of Hugging Face
    # models and the call will take a long time.
    if args.list_supported_hugging_face_models:
      if args.page_size is None:
        args.page_size = 100

    with endpoint_util.AiplatformEndpointOverrides(
        version, region='us-central1'
    ):
      mg_client = client_mg.ModelGardenClient(version)
      return mg_client.ListPublisherModels(
          limit=args.limit,
          batch_size=args.page_size,
          list_hf_models=args.list_supported_hugging_face_models,
          model_filter=args.model_filter,
      )
