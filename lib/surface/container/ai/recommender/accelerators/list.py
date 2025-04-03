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
"""Lists compatible accelerator profiles for GKE recommender."""

from googlecloudsdk.api_lib.ai.recommender import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log

_EXAMPLES = """
To list compatible accelerator profiles for a model, run:

$ {command} --model=deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
"""


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.Command):
  """List compatible accelerator profiles.

  This command lists all supported accelerators with their performance details.
  By default, the supported accelerators are displayed in a table format with
  select information for each accelerator. To see all details, use
  --format=yaml.

  To get supported model, model servers, and model server versions, run `gcloud
  alpha container ai recommender models list`, `gcloud alpha container ai
  recommender model-servers list`, and `gcloud alpha container ai recommender
  model-server-versions list`.
  Alternatively, run `gcloud alpha container ai recommender
  model-and-server-combinations list` to get all supported model and server
  combinations.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        "--model",
        required=True,
        help="The model.",
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
            " latest version."
        ),
    )
    parser.add_argument(
        "--max-ntpot-milliseconds",
        type=int,
        help=(
            "The maximum normalized time per output token (NTPOT) in"
            " milliseconds. NTPOT is measured as the request_latency /"
            " output_tokens. If this field is set, the command will only return"
            " accelerators that can meet the target ntpot milliseconds and"
            " display their throughput performance at the target latency."
            " Otherwise, the command will return all accelerators and display"
            " their highest throughput performance."
        ),
    )
    parser.add_argument(
        "--format",
        choices=["table", "yaml"],
        default="table",
        help=(
            "The output format. Default is table, which displays select"
            " information in a table format. Use --format=yaml to display all"
            " details."
        ),
    )

  def Run(self, args):
    client = util.GetClientInstance(base.ReleaseTrack.ALPHA)
    messages = util.GetMessagesModule(base.ReleaseTrack.ALPHA)

    try:
      request = messages.GkerecommenderAcceleratorsListRequest(
          modelName=args.model,
          modelServerName=args.model_server,
          modelServerVersion=args.model_server_version,
          performanceRequirements_maxNtpotMilliseconds=args.max_ntpot_milliseconds,
      )
      response = client.accelerators.List(request)
      if response.acceleratorOptions:
        return response.acceleratorOptions
      else:
        return []
    except exceptions.Error as e:
      log.error(f"An error has occurred: {e}")
      log.status.Print(f"An error has occurred: {e}")
      return []

  def Display(self, args, resources):
    if not resources:
      log.out.Print("No compatible accelerator profiles found.")
      return

    log.out.Print("Supported accelerators:")
    if args.format == "yaml":
      for item in resources:
        log.out.Print(item)
      return

    table_data = []
    for item in resources:
      row = {
          "model": (
              item.modelAndModelServerInfo.modelName
              if item.modelAndModelServerInfo
              else ""
          ),
          "model server": (
              item.modelAndModelServerInfo.modelServerName
              if item.modelAndModelServerInfo
              else ""
          ),
          "model server version": (
              item.modelAndModelServerInfo.modelServerVersion
              if item.modelAndModelServerInfo
              else ""
          ),
          "accelerator": item.acceleratorType,
          "accelerator count": (
              item.resourcesUsed.acceleratorCount if item.resourcesUsed else ""
          ),
          "output tokens per second": (
              item.performanceStats.outputTokensPerSecond
              if item.performanceStats
              else ""
          ),
          "ntpot ms": (
              item.performanceStats.ntpotMilliseconds
              if item.performanceStats
              else ""
          ),
      }
      table_data.append(row)

    headers = [
        "accelerator",
        "model",
        "model server",
        "model server version",
        "accelerator count",
        "output tokens per second",
        "ntpot ms",
    ]

    col_widths = {
        header: max(
            [len(str(row.get(header, ""))) for row in table_data]
            + [len(header)]
        )
        for header in headers
    }

    header_row = " | ".join(
        [f"{header:<{col_widths[header]}}" for header in headers]
    )
    log.out.Print(header_row)

    separator = "-|-".join(["-" * col_widths[header] for header in headers])
    log.out.Print(separator)

    for row in table_data:
      row_str = " | ".join([
          f"{str(row.get(header, '')):<{col_widths[header]}}"
          for header in headers
      ])
      log.out.Print(row_str)

    log.out.Print("\nFor more details on each accelerator, use --format=yaml")
