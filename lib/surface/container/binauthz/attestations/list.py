# Copyright 2017 Google Inc. All Rights Reserved.
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
"""The List command for Binary Authorization signatures."""

from googlecloudsdk.api_lib.container import binauthz_util as binauthz_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import binauthz_util as binauthz_command_util
from googlecloudsdk.command_lib.container.binauthz import flags as binauthz_flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class List(base.ListCommand):
  r"""List Binary Authorization attestations.

  This command lists Binary Authorization attestations for your project.
  Command line flags specify which artifact to list the attestations for.
  If no artifact is specified, then this lists all URLs with associated
  occurrences.  Note that the listed occurrences might include more than just
  attestations, since it is listing any occurrence at all that has the provided
  `--artifact-url`.

  ## EXAMPLES

  To attest an artifact by associating a signature to it, run:

      $ {command} \
          --artifact-url='gcr.io/example-project/example-image@sha256:abcd'
  """

  @staticmethod
  def Args(parser):
    binauthz_flags.AddCommonFlags(parser)

  def Run(self, args):
    project_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.Get(required=True),
        collection='cloudresourcemanager.projects')
    container_analysis_client = binauthz_api_util.ContainerAnalysisClient()
    if args.artifact_url:
      normalized_artifact_url = binauthz_command_util.NormalizeArtifactUrl(
          args.artifact_url)
      return container_analysis_client.YieldSignatures(
          project_ref=project_ref, artifact_url=normalized_artifact_url)
    else:
      return container_analysis_client.YieldUrlsWithOccurrences(project_ref)
