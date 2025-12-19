# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Lists supported use cases for GKE Inference Quickstart."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.ai.recommender import util
from googlecloudsdk.api_lib.util import exceptions as api_lib_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import commands


_EXAMPLES = """
To list all supported use cases, run:

$ {command}
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(commands.List):
  """List supported use cases that were used to generate the inference profiles."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(
        "table(useCase,averageInputLength,averageOutputLength)"
    )

  def Run(self, _):
    client = util.GetClientInstance(base.ReleaseTrack.GA)
    messages = util.GetMessagesModule(base.ReleaseTrack.GA)

    try:
      response = client.useCases.Fetch(
          messages.FetchUseCasesRequest()
      )
      if response.workloadSpecs:
        return response.workloadSpecs
      else:
        return []
    except apitools_exceptions.HttpError as error:
      raise api_lib_exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)
