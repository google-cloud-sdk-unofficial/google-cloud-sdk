# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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

"""Command to generate optimized Kubernetes manifests for a workload profile."""

from googlecloudsdk.api_lib.ai.recommender import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_printer_base
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.util import files


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class Create(base.Command):
  """Generate optimized Kubernetes manifests for a given workload profile."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        "--workload",
        type=str,
        required=True,
        help="""\
        The name of the optimization set to generate the manifest for.
        This specifies the workload, workload version, and workload
        characterization to optimize for (e.g., "redis-7-caching").
        """,
    )
    parser.add_argument(
        "--cluster-version",
        type=str,
        required=True,
        help="The GKE version to generate the manifest for.",
    )
    parser.add_argument(
        "--options",
        metavar="KEY=VALUE",
        type=arg_parsers.ArgDict(),
        help=(
            "Additional key-value pair options for generating the manifest. "
            "For example, to specify allowed machine types: "
            "--options=machineType=type1,type2"
        ),
        required=False,
    )
    parser.add_argument(
        "--output",
        choices=["manifest", "all"],
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
    parser.display_info.AddFormat("manifests")
    resource_printer.RegisterFormatter("manifests", ManifestPrinter)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = util.GetClientInstance(base.ReleaseTrack.ALPHA)
    messages = util.GetMessagesModule(base.ReleaseTrack.ALPHA)

    options = []
    if args.options:
      for key, value in args.options.items():
        options.append(
            messages.GoogleCloudGkerecommenderV1alpha1Option(
                key=key, value=value
            )
        )

    req = messages.GoogleCloudGkerecommenderV1alpha1GenerateOptimizedManifestRequest(
        optimizationSet=args.workload,
        clusterVersion=args.cluster_version,
        options=options,
    )

    resp = client.v1alpha1.GenerateOptimizedManifest(req)

    if args.output_path:
      _SaveOutputToFile(resp, args, args.output_path)

    return resp


def _SaveOutputToFile(resp, args, output_path):
  """Saves the output content to a file."""
  try:
    with files.FileWriter(output_path) as f:
      if args.output in ("manifest", "all"):
        resource_printer.Print(
            resource_projector.MakeSerializable(resp),
            "manifests",
            out=f,
            single=True,
        )
    log.status.Print(f"Output saved to {output_path}")
  except exceptions.Error as e:
    log.error(f"An error occurred while saving output to file: {e}")


class ManifestPrinter(resource_printer_base.ResourcePrinter):
  """Renders Kubernetes manifests."""

  def _AddRecord(self, record, delimit=True):
    """Renders the resource output."""
    if not record:
      return

    parts = []
    for manifest in record.get("kubernetesManifests", []):
      parts.extend([manifest.get("content", ""), "---"])

    if parts:
      self._out.write("\n".join(parts) + "\n")
