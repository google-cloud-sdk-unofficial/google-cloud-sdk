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
  occurrences.

  To list attestations with kind=ATTESTATION_AUTHORITY (v2), the
  attestation authority note ID must be passed with the flag `--attestation-
  authority-note-id`.  In this mode, only attestations bound to the provided
  note will be listed.  The returned attestation occurrences can be from any
  project, so the global `--project` flag is not required (or used) in this
  mode.

  To list attestations with kind=BUILD_DETAILS (v1, soon to be
  deprecated), the global --project flag must be provided (or implicitly
  provided from configuration).  In this mode, note that listed occurrences
  might include more than just attestations, since it is listing any occurrence
  at all that has the provided `--artifact-url`.  All listed occurrences will be
  from the provided project.

  ## EXAMPLES

  List all artifact URLs for which a v2 attestation exists and is bound
  to the passed attestation authority note:

      $ {command} \
          --attestation-authority-note=providers/example-prj/notes/note-id

  List the (pgp_key_fingerprint, signature) pairs for all v2
  attestations for the passed artifact-url bound to the passed attestation
  authority note:

      $ {command} \
          --attestation-authority-note=providers/exmple-prj/notes/note-id \
          --artifact-url='gcr.io/example-project/example-image@sha256:abcd'

  List all artifact URLs for which an v1 attestation exists in the
  passed project:

      $ {command} --project=example-project

  List the (public_key, signature) pairs for all v1 attestations in the
  passed project:

      $ {command} \
          --project=example-project \
          --artifact-url='gcr.io/example-project/example-image@sha256:abcd'
  """

  @staticmethod
  def Args(parser):
    binauthz_flags.AddListFlags(parser)

  def RunLegacy(self, normalized_artifact_url):
    project_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.Get(required=True),
        collection='cloudresourcemanager.projects')
    client = binauthz_api_util.ContainerAnalysisLegacyClient()
    if normalized_artifact_url:
      return client.YieldSignatures(
          project_ref=project_ref, artifact_url=normalized_artifact_url)
    else:
      return client.YieldUrlsWithOccurrences(project_ref)

  def Run(self, args):
    normalized_artifact_url = None
    if args.artifact_url:
      normalized_artifact_url = binauthz_command_util.NormalizeArtifactUrl(
          args.artifact_url)

    if not args.attestation_authority_note:
      return self.RunLegacy(normalized_artifact_url)

    attestation_authority_note_ref = (
        args.CONCEPTS.attestation_authority_note.Parse())

    client = binauthz_api_util.ContainerAnalysisClient()

    if normalized_artifact_url:
      return client.YieldPgpKeyFingerprintsAndSignatures(
          note_ref=attestation_authority_note_ref,
          artifact_url=normalized_artifact_url,
      )
    else:
      return client.YieldUrlsWithOccurrences(attestation_authority_note_ref)
