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
"""Lists supported model and server combinations for GKE recommender."""

from googlecloudsdk.api_lib.ai.recommender import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log

_EXAMPLES = """
To list all supported model and server combinations, run:

$ {command}
"""


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.Command):
  """List supported model and server combinations.

  This command lists all supported model, model server, and model server version
    combinations.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        "--model",
        help="The model. If not specified, this defaults to any model.",
    )
    parser.add_argument(
        "--model-server",
        help=(
            "The model server. If not specified, this defaults to any model"
            " server."
        ),
    )
    parser.add_argument(
        "--model-server-version",
        help=(
            "The model server version. If not specified, this defaults to the"
            " any model server version."
        ),
    )

  def Run(self, args):
    client = util.GetClientInstance(base.ReleaseTrack.ALPHA)
    messages = util.GetMessagesModule(base.ReleaseTrack.ALPHA)

    try:
      request = messages.GkerecommenderModelsAndServersListRequest(
          modelName=args.model,
          modelServerName=args.model_server,
          modelServerVersion=args.model_server_version,
      )
      response = client.modelsAndServers.List(request)
      if response.modelAndModelServerInfo:
        return response.modelAndModelServerInfo
      else:
        return []
    except exceptions.Error as e:
      log.error(f"An error has occurred: {e}")
      log.status.Print(f"An error has occurred: {e}")
      return []

  def Display(self, _, resources):
    if not resources:
      log.out.Print("No supported model and model server combinations found.")
      return

    log.out.Print("Supported model and model server combinations:")

    table_data = [
        {
            "Model": item.modelName,
            "Model Server": item.modelServerName,
            "Model Server Version": item.modelServerVersion,
        }
        for item in resources
    ]

    col_widths = {
        "Model": max(
            [len(row["Model"]) for row in table_data] + [len("Model")]
        ),
        "Model Server": max(
            [len(row["Model Server"]) for row in table_data]
            + [len("Model Server")]
        ),
        "Model Server Version": max(
            [len(row["Model Server Version"]) for row in table_data]
            + [len("Model Server Version")]
        ),
    }

    header = " | ".join([
        f"{'Model':<{col_widths['Model']}}",
        f"{'Model Server':<{col_widths['Model Server']}}",
        f"{'Model Server Version':<{col_widths['Model Server Version']}}",
    ])
    log.out.Print(header)

    separator = "-|-".join([
        "-" * col_widths["Model"],
        "-" * col_widths["Model Server"],
        "-" * col_widths["Model Server Version"],
    ])
    log.out.Print(separator)

    for row in table_data:
      row_str = " | ".join([
          f"{row['Model']:<{col_widths['Model']}}",
          f"{row['Model Server']:<{col_widths['Model Server']}}",
          (
              f"{row['Model Server Version']:<{col_widths['Model Server Version']}}"
          ),
      ])
      log.out.Print(row_str)
