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
"""The Create command for Binary Authorization attestations."""

from googlecloudsdk.api_lib.container import binauthz_util as binauthz_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import binauthz_util as binauthz_command_util
from googlecloudsdk.command_lib.container.binauthz import flags as binauthz_flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files


class Create(base.CreateCommand):
  r"""Create a Binary Authorization attestation.

  This command creates a Binary Authorization attestation for your project.
  The created attestation is tied to an artifact specified in command line
  flags.

  ## v2 (kind=BUILD_DETAILS) Attestations

  To create an attestations with kind=ATTESTATION_AUTHORITY ("v2"), the
  attestation authority note ID must be passed with the flag `--attestation-
  authority-note-id`.  In this mode, the created attestation will be bound to
  the passed note (attestation authority).  The `--project` flag is required,
  since the attestation can be created in any project, regardless of which
  project the attestation authority lives in, or which project the attested
  image lives in.

  When creating attestations with kind=ATTESTATION_AUTHORITY, the following
  parameters must be provided:

    * --attestation-authority-note.  This note with
    kind=ATTESTATION_AUTHORITY must exist and the principal gcloud is
    authenticated as (core/account) must have the
    `containeranalysis.notes.attachOccurrence` permission for the note resource
    (usually via the `containeranalysis.notes.attacher` role).
    * --artifact-url (This is always required).  Note that there are no
    restrictions on the project or registry.
    * --signature-file (This is always required).
    * --project (or core/project must be set).  This is the project the
    attestation occurrence will be created in.
    * --pgp-key-fingerprint.

  But `--public-key-file` must NOT be provided, as its purpose is superseded by
  `--pgp-key-fingerprint`.

  ## v1 (kind=BUILD_DETAILS) Attestations

  To create an attestation with kind=BUILD_DETAILS ("v1", soon to be
  deprecated), do not pass `--attestation-authority-note`.  The occurrence
  will be created in the project passed via `--project` (or core/project), but
  it is important to note that Binary Authorization only looks in the project
  that the GCR image (via `--artifact-url`) lives in when searching for
  BUILD_DETAILS occurrences.  Therefore `--project` must match the project in
  `--artifact-url` for BinAuthz verification to work.

  When creating attestations with kind=BUILD_DETAILS, the following
  parameters must be provided:

    * --artifact-url (This is always required).
    * --signature-file (This is always required).
    * --project (or core/project must be set).  This is the project the
    attestation occurrence will be created in.  This should almost always been
    the same project as the GCR image in `--artifact-url`.
    * --public-key-file.

  But `--attestation-authority-note` and `--pgp-key-fingerprint` must NOT
  be provided, as they only apply to v2 kind=ATTESTATION_AUTHORITY attestations.

  ## EXAMPLES

  To create a v1 attestation (kind=BUILD_DETAILS) by associating a
  signature to an artifact, run:

      $ {command} \
          --artifact-url='gcr.io/example-project/example-image@sha256:abcd' \
          --signature-file=signed_artifact_attestation.pgp.sig \
          --public-key-file=my_public_key.pgp.pub

  To create a v2 attestation (kind=ATTESTATION_AUTHORITY) as the
  attestation authority represented by an ATTESTATION_AUTHORITY note with
  resource path "providers/exmple-prj/notes/note-id" by associating a signature
  to an artifact, run:

      $ {command} \
          --artifact-url='gcr.io/example-project/example-image@sha256:abcd' \
          --attestation-authority-note=providers/exmple-prj/notes/note-id \
          --signature-file=signed_artifact_attestation.pgp.sig \
          --pgp-key-fingerprint=AAAA0000000000000000FFFFFFFFFFFFFFFFFFFF
  """

  @staticmethod
  def Args(parser):
    binauthz_flags.AddCreateAttestationFlags(parser)

  def CreateLegacyAttestation(
      self,
      project_ref,
      normalized_artifact_url,
      signature,
      public_key_file,
  ):
    public_key = files.GetFileContents(public_key_file)
    provider_ref = binauthz_command_util.CreateProviderRefFromProjectRef(
        project_ref)
    note_id = binauthz_command_util.NoteId(
        artifact_url=normalized_artifact_url,
        public_key=public_key,
        signature=signature,
    )
    provider_note_ref = binauthz_command_util.ParseProviderNote(
        note_id=note_id,
        provider_ref=provider_ref,
    )
    return binauthz_api_util.ContainerAnalysisLegacyClient().PutSignature(
        occurrence_project_ref=project_ref,
        provider_ref=provider_ref,
        provider_note_ref=provider_note_ref,
        note_id=note_id,
        artifact_url=normalized_artifact_url,
        public_key=public_key,
        signature=signature,
    )

  def Run(self, args):
    project_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.Get(required=True),
        collection='cloudresourcemanager.projects',
    )
    normalized_artifact_url = binauthz_command_util.NormalizeArtifactUrl(
        args.artifact_url)
    signature = console_io.ReadFromFileOrStdin(
        args.signature_file, binary=False)

    if args.attestation_authority_note:
      client = binauthz_api_util.ContainerAnalysisClient()
      return client.CreateAttestationOccurrence(
          project_ref=project_ref,
          note_ref=args.CONCEPTS.attestation_authority_note.Parse(),
          artifact_url=normalized_artifact_url,
          pgp_key_fingerprint=args.pgp_key_fingerprint,
          signature=signature,
      )
    else:
      return self.CreateLegacyAttestation(
          project_ref=project_ref,
          normalized_artifact_url=normalized_artifact_url,
          signature=signature,
          public_key_file=args.public_key_file,
      )
