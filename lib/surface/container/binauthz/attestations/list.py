# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.container import binauthz_util as binauthz_api_util
from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import authorities
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import binauthz_util as binauthz_command_util
from googlecloudsdk.command_lib.container.binauthz import flags
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(base.ListCommand):
  r"""List Binary Authorization attestations.

  This command lists Binary Authorization attestations for your project.
  Command line flags specify which artifact to list the attestations for.
  If no artifact is specified, then this lists all URLs with associated
  occurrences.

  ## EXAMPLES

  List all artifact URLs for which an attestation exists and is bound to the
  passed attestation authority:

      $ {command} \
          --attestation-authority=projects/foo/attestationAuthorities/bar

  List the (pgp_key_fingerprint, signature) pairs for all attestations for the
  passed artifact-url bound to the passed attestation authority:

      $ {command} \
          --attestation-authority=projects/foo/attestationAuthorities/bar \
          --artifact-url='gcr.io/foo/example-image@sha256:abcd'
  """

  @staticmethod
  def Args(parser):
    flags.AddArtifactUrlFlag(parser, required=False)

    mutex_group = parser.add_mutually_exclusive_group(required=True)
    flags.AddConcepts(
        mutex_group,
        flags.GetAuthorityPresentationSpec(
            base_name='attestation-authority',
            required=False,  # one-of requirement is set in mutex_group.
            positional=False,
            use_global_project_flag=False,
            group_help=textwrap.dedent("""\
              The Attestation Authority whose Container Analysis Note will be
              queried for attestations. Note that the caller must have the
              `containeranalysis.notes.listOccurrences` permission on the note
              being queried.""")
        ),
        flags.GetAuthorityNotePresentationSpec(
            base_name='attestation-authority-note',
            required=False,  # one-of requirement is set in mutex_group.
            positional=False,
            group_help=textwrap.dedent("""\
              The Container Analysis ATTESTATION_AUTHORITY Note that will be
              queried for attestations.  When this option is passed, only
              occurrences with kind ATTESTATION_AUTHORITY will be returned.  The
              occurrences might be from any project, not just the project where
              the note lives.  Note that the caller must have the
              `containeranalysis.notes.listOccurrences` permission on the note
              being queried.""")
        ),
    )

  def Run(self, args):
    normalized_artifact_url = None
    if args.artifact_url:
      normalized_artifact_url = binauthz_command_util.NormalizeArtifactUrl(
          args.artifact_url)

    note_ref = args.CONCEPTS.attestation_authority_note.Parse()
    if note_ref is None:
      authority_ref = args.CONCEPTS.attestation_authority.Parse()
      api_version = apis.GetApiVersion(self.ReleaseTrack())
      authority = authorities.Client(api_version).Get(authority_ref)
      # TODO(b/79709480): Add other types of authorities if/when supported.
      note_ref = resources.REGISTRY.ParseResourceId(
          'containeranalysis.projects.notes',
          authority.userOwnedDrydockNote.noteReference, {})

    client = binauthz_api_util.ContainerAnalysisClient()

    if normalized_artifact_url:
      return client.YieldPgpKeyFingerprintsAndSignatures(
          note_ref=note_ref,
          artifact_url=normalized_artifact_url,
      )
    else:
      return client.YieldUrlsWithOccurrences(note_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(base.ListCommand):
  r"""List Binary Authorization attestations.

  This command lists Binary Authorization attestations for your project.
  Command line flags specify which artifact to list the attestations for.
  If no artifact is specified, then this lists all URLs with associated
  occurrences.

  ## EXAMPLES

  List all artifact URLs for which an attestation exists and is bound to the
  passed attestor:

      $ {command} \
          --attestor=projects/foo/attestor/bar

  List the (pgp_key_fingerprint, signature) pairs for all attestations for the
  passed artifact-url bound to the passed attestor:

      $ {command} \
          --attestor=projects/foo/attestors/bar \
          --artifact-url='gcr.io/foo/example-image@sha256:abcd'
  """

  @staticmethod
  def Args(parser):
    flags.AddArtifactUrlFlag(parser, required=False)

    flags.AddConcepts(
        parser,
        flags.GetAttestorPresentationSpec(
            base_name='attestor',
            required=True,
            positional=False,
            use_global_project_flag=False,
            group_help=textwrap.dedent("""\
              The Attestor whose Container Analysis Note will be queried
              for attestations. Note that the caller must have the
              `containeranalysis.notes.listOccurrences` permission on the note
              being queried.""")
        ),
    )

  def Run(self, args):
    normalized_artifact_url = None
    if args.artifact_url:
      normalized_artifact_url = binauthz_command_util.NormalizeArtifactUrl(
          args.artifact_url)

    attestor_ref = args.CONCEPTS.attestor.Parse()
    api_version = apis.GetApiVersion(self.ReleaseTrack())
    attestor = authorities.Client(api_version).Get(attestor_ref)
    # TODO(b/79709480): Add other types of attestors if/when supported.
    note_ref = resources.REGISTRY.ParseResourceId(
        'containeranalysis.projects.notes',
        attestor.userOwnedDrydockNote.noteReference, {})

    client = binauthz_api_util.ContainerAnalysisClient()

    if normalized_artifact_url:
      return client.YieldPgpKeyFingerprintsAndSignatures(
          note_ref=note_ref,
          artifact_url=normalized_artifact_url,
      )
    else:
      return client.YieldUrlsWithOccurrences(note_ref)
