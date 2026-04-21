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
"""Command to create an image streaming cache."""

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
class Create(base.CreateCommand):
  """Initiates the prewarming of a specified artifact version or tag."""

  detailed_help = {
      "DESCRIPTION": (
          """
          {description}
      """
      ),
      "EXAMPLES": (
          """
          # Prewarm a version by full resource name in a specific stream location
          $ {command} projects/my-proj/locations/us-central1/repositories/my-repo/packages/my-pkg/versions/sha256:abc123 --stream-location=us-east1

          # Prewarm a tagged artifact in the repository's region, asynchronously
          $ {command} --package=my-pkg --tag=latest --location=us-central1 --repository=my-repo --stream-location=us-east1

          # Prewarm with custom retention and force
          $ {command} --package=my-pkg --version=sha256:abc123 --repository=my-repo --location=us-west1 --stream-location=us-west1 --retention-days=7 --force
      """
      ),
  }

  @staticmethod
  def Args(parser):
    flags.GetStreamLocationArg().AddToParser(parser)
    flags.GetForceArg().AddToParser(parser)
    flags.GetRetentionDaysArg().AddToParser(parser)

    resource_group = parser.add_group(mutex=True, required=True)

    resource_group.add_argument(
        "ARTIFACT",
        nargs="?",
        help="The full resource name of the version or tag to prewarm.",
    )

    flag_group = resource_group.add_group()

    # 4. Inject the ConceptParsers into the nested mutex group!
    concept_parsers.ConceptParser(
        [
            presentation_specs.ResourcePresentationSpec(
                "--package",
                flags.GetPackageResourceSpec(),
                "The package to prewarm.",
                group=flag_group,
            ),
        ],
        command_level_fallthroughs={},
    ).AddToParser(parser)

    # Mutex group for EITHER --version or --tag ID
    version_or_tag_group = flag_group.add_group(mutex=True, required=True)
    version_or_tag_group.add_argument(
        "--version",
        help="The version ID to prewarm (e.g., 'sha256:abc123').",
    )
    version_or_tag_group.add_argument(
        "--tag",
        help="The tag name to prewarm (e.g., 'latest').",
    )

  def Run(self, args):
    client = ar_requests.GetClient()
    messages = ar_requests.GetMessages()

    # Option A: User provided the positional argument
    if args.ARTIFACT:
      artifact_ref = args.ARTIFACT
      if "/versions/" in artifact_ref:
        artifact_type = "version"
      elif "/tags/" in artifact_ref:
        artifact_type = "tag"
      else:
        raise ar_exceptions.InvalidInputValueError(
            "Invalid artifact resource name: {}".format(artifact_ref)
        )
    # Option B: User used the component flags
    else:
      package_concept = args.CONCEPTS.package.Parse()
      if not package_concept:
        # This case should ideally be caught by 'required=True' in the spec
        raise ar_exceptions.InvalidInputValueError(
            "Missing required flags for the package (e.g., --package,"
            " --repository, --location)."
        )

      package_name = package_concept.RelativeName()

      if args.IsSpecified("version"):
        artifact_ref = "{}/versions/{}".format(package_name, args.version)
        artifact_type = "version"
      elif args.IsSpecified("tag"):
        artifact_ref = "{}/tags/{}".format(package_name, args.tag)
        artifact_type = "tag"
      else:
        # Should not happen due to the required mutex group
        raise ar_exceptions.InvalidInputValueError(
            "Either --version or --tag must be specified with component flags."
        )

    try:
      operation = ar_requests.PrewarmArtifact(
          client,
          messages,
          artifact_ref,
          artifact_type,
          args.stream_location,
          args.retention_days,
          args.force,
      )
      log.status.Print(
          "Prewarming request issued for [{}]. Operation: [{}]".format(
              artifact_ref, operation.name
          )
      )
      return operation
    except ar_exceptions.ArtifactRegistryError as e:
      raise e
