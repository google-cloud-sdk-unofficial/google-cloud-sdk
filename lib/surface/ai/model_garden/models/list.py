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
            format("{0:s}/{1:s}", name, versionId).sub("publishers/", "").sub("models/", "").if(NOT include_supported_hugging_face_models):sort=1:label=MODEL,
            name.sub("publishers/hf-", "").sub("models/", "").if(include_supported_hugging_face_models):sort=1:label=HUGGING_FACE_MODEL,
            supportedActions.multiDeployVertex.yesno(yes=Yes):label=SUPPORTS_DEPLOYMENT
        )
    """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class List(base.ListCommand):
  """List the publisher models in Model Garden."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(_DEFAULT_FORMAT)
    parser.add_argument(
        '--include-supported-hugging-face-models',
        action='store_true',
        default=False,
        required=False,
        help='Whether to also list supported Hugging Face models.',
    )

  def Run(self, args):
    version = constants.BETA_VERSION
    with endpoint_util.AiplatformEndpointOverrides(
        version, region='us-central1'
    ):
      mg_client = client_mg.ModelGardenClient(version)
      return mg_client.ListPublisherModels(
          limit=args.limit,
          include_hf_models=args.include_supported_hugging_face_models,
      )
