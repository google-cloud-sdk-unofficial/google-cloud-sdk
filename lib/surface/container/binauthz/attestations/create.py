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
from googlecloudsdk.core.util import files


class Create(base.CreateCommand):
  r"""Create a Binary Authorization attestation.

  This command creates a Binary Authorization attestation for your project.
  The created attestation is tied to an artifact specified in command line
  flags.

  ## EXAMPLES

  To attest an artifact by associating a signature to it, run:

      $ {command} \
          --artifact-url='gcr.io/example-project/example-image@sha256:abcd' \
          --signature-file=signed_artifact_attestation.pgp.sig \
          --public-key-file=my_public_key.pgp.pub
  """

  @staticmethod
  def Args(parser):
    binauthz_flags.AddCommonFlags(parser)
    binauthz_flags.AddSignatureSpecifierFlags(parser)

  def Run(self, args):
    project_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.Get(required=True),
        collection='cloudresourcemanager.projects')
    normalized_artifact_url = binauthz_command_util.NormalizeArtifactUrl(
        args.artifact_url)
    public_key = files.GetFileContents(args.public_key_file)
    signature = files.GetFileOrStdinContents(args.signature_file)
    note_id = binauthz_command_util.NoteId(normalized_artifact_url, public_key,
                                           signature)
    provider_ref = binauthz_command_util.CreateProviderRefFromProjectRef(
        project_ref)
    provider_note_ref = binauthz_command_util.ParseProviderNote(
        note_id=note_id, provider_ref=provider_ref)
    return binauthz_api_util.ContainerAnalysisClient().PutSignature(
        occurrence_project_ref=project_ref,
        provider_ref=provider_ref,
        provider_note_ref=provider_note_ref,
        note_id=note_id,
        artifact_url=normalized_artifact_url,
        public_key=public_key,
        signature=signature)
