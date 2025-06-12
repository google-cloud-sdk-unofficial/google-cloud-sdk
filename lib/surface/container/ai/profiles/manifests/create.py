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
"""Generates optimized Kubernetes manifests for GKE Inference Quickstart."""

from googlecloudsdk.api_lib.ai.recommender import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Generate ready-to-deploy Kubernetes manifests with compute, load balancing, and autoscaling capabilities.

  To get supported model, model servers, and model server versions, run `gcloud
  alpha container ai profiles model-and-server-combinations list`. To get
  supported accelerators with their performance metrics, run `gcloud alpha
  container ai profiles accelerators list`.
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
        help="The model server.",
    )
    parser.add_argument(
        "--model-server-version",
        help=(
            "The model server version. If not specified, this defaults to the"
            " latest version."
        ),
    )
    parser.add_argument(
        "--target-ntpot-milliseconds",
        type=int,
        help=(
            "The maximum normalized time per output token (NTPOT) in"
            " milliseconds. NTPOT is measured as the request_latency /"
            " output_tokens. If this is set, the manifests will include"
            " Horizontal Pod Autoscaler (HPA) resources which automatically"
            " adjust the model server replica count in response to changes in"
            " model server load to keep p50 NTPOT below the specified"
            " threshold. If the provided target-ntpot-milliseconds is too low"
            " to achieve, the HPA manifest will not be generated. "
        ),
    )
    parser.add_argument(
        "--accelerator-type",
        required=True,
        help="The accelerator type.",
    )
    parser.add_argument(
        "--namespace",
        help=(
            "The namespace to deploy the manifests in. Default namespace is"
            " 'default'."
        ),
    )
    parser.add_argument(
        "--output",
        choices=["manifest", "comments", "all"],
        default="all",
        help="The output to display. Default is all.",
    )
    parser.add_argument(
        "--output-path",
        help=(
            "The path to save the output to. If not specified, output to the"
            " terminal."
        ),
    )

  def Run(self, args):
    client = util.GetClientInstance(base.ReleaseTrack.ALPHA)
    messages = util.GetMessagesModule(base.ReleaseTrack.ALPHA)

    try:
      request = messages.GkerecommenderOptimizedManifestRequest(
          modelAndModelServerInfo_modelName=args.model,
          modelAndModelServerInfo_modelServerName=args.model_server,
          modelAndModelServerInfo_modelServerVersion=args.model_server_version,
          targetNtpotMilliseconds=args.target_ntpot_milliseconds,
          acceleratorType=args.accelerator_type,
          kubernetesNamespace=args.namespace,
      )
      response = client.v1alpha1.OptimizedManifest(request)
      return response
    except exceptions.Error as e:
      log.error(f"An error has occurred: {e}")
      log.status.Print(f"An error has occurred: {e}")
      return []

  def Display(self, args, resources):
    if not resources:
      log.out.Print("No manifests generated.")
      return

    output_content = ""
    if args.output == "manifest" or args.output == "all":
      for manifest in resources.k8sManifests:
        output_content += manifest.content + "\n---\n"

    if args.output == "comments" or args.output == "all":
      if resources.comments:
        comment_string = "\n".join([f"# {line}" for line in resources.comments])
        output_content += comment_string

    if args.output_path:
      try:
        with files.FileWriter(args.output_path, output_content) as f:
          f.write(output_content)
        log.out.Print(f"Output saved to {args.output_path}")
      except exceptions.Error as e:
        log.error(f"An error occurred while saving output to file: {e}")
    else:
      log.out.Print(output_content)
