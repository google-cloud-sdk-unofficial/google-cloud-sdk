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
"""Lists supported model servers for GKE Inference Quickstart."""

from googlecloudsdk.api_lib.ai.recommender import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import commands
from googlecloudsdk.command_lib.run.printers import profiles_csv_printer
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer

_EXAMPLE = """
To list all supported model servers for a model, run:

$ {command} --model=deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
"""


def amount_to_decimal(cost):
  """Converts cost to a decimal representation."""
  units = cost.units
  if not units:
    units = 0
  decimal_value = +(units + cost.nanos / 1e9)
  return f"{decimal_value:.3f}"


def get_decimal_cost(costs):
  """Returns the cost per million normalized output tokens as a decimal.

  Args:
    costs: The costs to convert.
  """
  output_token_cost = "N/A"
  if costs and costs[0].costPerMillionOutputTokens:
    output_token_cost = amount_to_decimal(
        costs[0].costPerMillionOutputTokens
    )
  input_token_cost = "N/A"
  if costs and costs[0].costPerMillionInputTokens:
    input_token_cost = amount_to_decimal(costs[0].costPerMillionInputTokens)
  return (input_token_cost, output_token_cost)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(commands.List):
  """List supported model servers for a given model.

  To get supported models, run `gcloud container ai profiles models
  list`.
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
        required=True,
        help=(
            "The model server."
        ),
    )
    parser.add_argument(
        "--model-server-version",
        help=(
            "The model server version. If not specified, this defaults to"
            " latest model server version."
        ),
    )
    parser.add_argument(
        "--instance-type",
        help=(
            "The instance type. If not specified, this defaults to any"
            "instance type."
        ),
    )
    parser.add_argument(
        "--format",
        help=(
            "The format to print the output in. Default is csvprofile, which"
            " displays the profile information in a CSV format, including"
            "cost conversions."
        ),
    )

    resource_printer.RegisterFormatter(
        profiles_csv_printer.PROFILES_PRINTER_FORMAT,
        profiles_csv_printer.ProfileCSVPrinter,
    )
    parser.display_info.AddFormat(
        profiles_csv_printer.PROFILES_PRINTER_FORMAT
    )

  def Run(self, args):
    client = util.GetClientInstance(base.ReleaseTrack.GA)
    messages = util.GetMessagesModule(base.ReleaseTrack.GA)

    try:
      request = messages.GkerecommenderGetBenchmarkingDataRequest(
          modelAndModelServerInfo_modelName=args.model,
          modelAndModelServerInfo_modelServerName=args.model_server,
          modelAndModelServerInfo_modelServerVersion=args.model_server_version,
          instanceType=args.instance_type,
      )
      response = client.v1.GetBenchmarkingData(request)
      if not response.profile:
        return []
      else:
        return response.profile
    except exceptions.Error as e:
      log.error(f"An error has occurred: {e}")
      log.status.Print(f"An error has occurred: {e}")
      return []
