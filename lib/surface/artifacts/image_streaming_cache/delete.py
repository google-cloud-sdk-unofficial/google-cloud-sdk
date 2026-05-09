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
"""Command to delete an image streaming cache."""

from googlecloudsdk.api_lib.artifacts import exceptions as ar_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import requests as ar_requests
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
@base.DefaultUniverseOnly
class Delete(base.DeleteCommand):
  """Removes the prewarmed state of a specific artifact from a specific stream location."""

  detailed_help = {
      "DESCRIPTION": """
          {description}
      """,
      "EXAMPLES": """
          # Removes the prewarmed state of a specific artifact using flags
          $ {command} --package=my-pkg --tag=latest --repository=my-repo --location=us-central1 --stream-location=us-east1

          # Using full resource name
          $ {command} projects/my-proj/locations/us-central1/repositories/my-repo/packages/my-pkg/versions/sha256:abc123 --stream-location=us-east1
      """,
  }

  @staticmethod
  def Args(parser):
    flags.GetStreamLocationArg().AddToParser(parser)

    resource_group = parser.add_group(mutex=True, required=True)
    resource_group.add_argument(
        "ARTIFACT",
        nargs="?",
        help="The full resource name of the version or tag to remove.",
    )

    flag_group = resource_group.add_group()

    concept_parsers.ConceptParser(
        [
            presentation_specs.ResourcePresentationSpec(
                "--package",
                flags.GetPackageResourceSpec(),
                "The package to remove.",
                group=flag_group,
            ),
        ],
        command_level_fallthroughs={},
    ).AddToParser(parser)

    # Mutex group for EITHER --version or --tag ID
    version_or_tag_group = flag_group.add_group(mutex=True, required=True)
    version_or_tag_group.add_argument(
        "--version",
        help="The version to remove (e.g., 'sha256:abc123').",
    )
    version_or_tag_group.add_argument(
        "--tag",
        help="The tag to remove (e.g., 'latest').",
    )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The image streaming cache deleted.
    """
    client = ar_requests.GetClient()
    messages = ar_requests.GetMessages()

    if args.ARTIFACT:
      artifact_ref = args.ARTIFACT
    else:
      package_concept = args.CONCEPTS.package.Parse()
      if not package_concept:
        raise ar_exceptions.InvalidInputValueError(
            "Missing required flags for the package (e.g., --package,"
            " --repository, --location)."
        )

      package_name = package_concept.RelativeName()

      if args.IsSpecified("version"):
        artifact_ref = f"{package_name}/versions/{args.version}"
      elif args.IsSpecified("tag"):
        artifact_ref = f"{package_name}/tags/{args.tag}"
      else:
        raise ar_exceptions.InvalidInputValueError(
            "Either --version or --tag must be specified with component flags."
        )

    result = ar_requests.RemovePrewarmedArtifact(
        client,
        messages,
        artifact_ref,
        args.stream_location,
    )
    log.status.Print(
        "Successfully removed image streaming cache for [{}] in [{}].".format(
            artifact_ref, args.stream_location
        )
    )
    return result
