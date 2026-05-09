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
"""Command to list image streaming caches."""

from googlecloudsdk.api_lib.artifacts import exceptions as ar_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import requests as ar_requests


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
@base.DefaultUniverseOnly
class List(base.ListCommand):
  """Lists artifacts that are prewarmed within a given repository."""

  detailed_help = {
      "DESCRIPTION": """
          {description}
      """,
      "EXAMPLES": """
          # List prewarmed artifacts for a specific stream location
          $ {command} --repository=my-repo --location=us-central1 --filter="stream_location=us-east1"
      """,
  }

  @staticmethod
  def Args(parser):
    flags.GetRepoFlag().AddToParser(parser)
    parser.display_info.AddFormat("table(uri, location, expirationTime)")

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A list of PrewarmedArtifact resources.
    """
    client = ar_requests.GetClient()
    messages = ar_requests.GetMessages()
    repository_ref = args.CONCEPTS.repository.Parse()

    try:
      resources = ar_requests.ListPrewarmedArtifacts(
          client,
          messages,
          repository_ref.RelativeName(),
          page_size=args.page_size,
          server_filter=args.filter,
      )
      # Prevent client-side filtering because server handles it
      args.filter = None
      return resources
    except ar_exceptions.ArtifactRegistryError as e:
      raise e
