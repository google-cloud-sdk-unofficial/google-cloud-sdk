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
"""Flags and concepts for Software Delivery Trust commands."""

import textwrap

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def GetAuthorityResourceSpec():
  """Constructs a ResourceSpec for an SD Trust Authority."""
  return concepts.ResourceSpec(
      'softwaredeliverytrust.projects.locations.authorities',
      resource_name='authority',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=concepts.ResourceParameterAttributeConfig(
          name='location',
          help_text='The Google Cloud location for the {resource}.',
      ),
      authoritiesId=concepts.ResourceParameterAttributeConfig(
          name='authority',
          help_text='The identifier of the {resource}.',
      ),
  )


def GetAuthorityPresentationSpec(
    group_help,
    required=True,
    positional=True,
):
  """Constructs a ResourcePresentationSpec for an Authority resource argument."""
  name = 'AUTHORITY' if positional else '--authority'
  return presentation_specs.ResourcePresentationSpec(
      name,
      GetAuthorityResourceSpec(),
      group_help=group_help,
      required=required,
  )


def AddAuthorityResourceArg(parser, group_help, required=True, positional=True):
  """Adds the Authority resource argument to the parser."""
  concept_parsers.ConceptParser(
      [GetAuthorityPresentationSpec(group_help, required, positional)]
  ).AddToParser(parser)


SIGNATURE_ALGORITHMS = [
    'ec-sign-p256-sha256',
    'ec-sign-p384-sha384',
    'ec-sign-p521-sha512',
    'rsa-sign-pss-2048-sha256',
    'rsa-sign-pss-3072-sha256',
    'rsa-sign-pss-4096-sha256',
    'rsa-sign-pss-4096-sha512',
    'rsa-sign-pkcs1-2048-sha256',
    'rsa-sign-pkcs1-3072-sha256',
    'rsa-sign-pkcs1-4096-sha256',
    'rsa-sign-pkcs1-4096-sha512',
]


def AddKeyDefinitionFlags(parser, required=False):
  """Adds flags for specifying a public key (either local file or Cloud KMS)."""
  key_group = parser.add_mutually_exclusive_group(required=required)

  # Group 1: Local PKIX public key file
  local_group = key_group.add_group(help='Local PKIX public key configuration')
  local_group.add_argument(
      '--pkix-public-key-file',
      help=(
          'Path to a local file containing the PEM-encoded PKIX'
          ' SubjectPublicKeyInfo public key.'
      ),
  )
  local_group.add_argument(
      '--signature-algorithm',
      choices=SIGNATURE_ALGORITHMS,
      help='The signature and digest algorithm used with the local public key.',
  )

  # Group 2: Cloud KMS key version
  kms_group = key_group.add_group(help='Cloud KMS public key configuration')
  kms_group.add_argument(
      '--kms-key-version',
      help=textwrap.dedent("""\
          The Cloud KMS CryptoKeyVersion resource name.
          Format: projects/{project}/locations/{location}/keyRings/{key_ring}/cryptoKeys/{key}/cryptoKeyVersions/{version}
      """),
  )

  # Optional key ID slot hint
  parser.add_argument(
      '--key-id',
      help=textwrap.dedent("""\
          Optional key slot identifier or signer key hint (max 512 characters).
          Must be unique within this authority. Defaults to the KMS key version
          resource name for KMS keys. For pkix-public-key-file, if omitted, will be left unassigned.
      """),
  )


def AddRemoveKeyFlags(parser):
  """Adds mutually exclusive flags for identifying a key to remove."""
  remove_group = parser.add_mutually_exclusive_group(required=True)
  remove_group.add_argument(
      '--key-id',
      help='The key identifier of the public key to remove from the authority.',
  )
  remove_group.add_argument(
      '--fingerprint',
      help=(
          'The RFC 6920 Named Information URI (SPKI SHA-256 fingerprint) of the'
          ' key to remove.'
      ),
  )
