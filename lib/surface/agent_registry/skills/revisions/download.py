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
"""Download skill revision payload."""

import os
import zipfile

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.agent_registry import download_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log


def ProjectAttributeConfig():
  return concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='The Cloud location for the {resource}.')


def SkillAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='skill', help_text='The Skill ID for the {resource}.')


def RevisionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='revision', help_text='The Revision ID for the {resource}.')


def GetSkillRevisionResourceSpec():
  return concepts.ResourceSpec(
      'agentregistry.projects.locations.skills.revisions',
      api_version='v1alpha',
      resource_name='revision',
      revisionsId=RevisionAttributeConfig(),
      skillsId=SkillAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=ProjectAttributeConfig(),
  )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.UniverseCompatible
class Download(base.Command):
  """Download the payload of a Skill Revision.

  Downloads the raw ZIP archive of a skill revision.
  """

  api_version = 'v1alpha'

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To download a revision named 'v1' for a skill named `my-skill` in `us-central1` to the local path `./my-skill-payload.zip`:

              $ {command} v1 --skill=my-skill --location=us-central1 --destination="./my-skill-payload.zip"
          """,
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            'revision',
            GetSkillRevisionResourceSpec(),
            'The Skill Revision to download.',
            required=True,
        )
    ]).AddToParser(parser)

    parser.add_argument(
        '--destination',
        required=True,
        help=(
            'The path (directory or file) where you want to download the'
            ' payload.'
        ),
    )

    parser.add_argument(
        '--allow-overwrite',
        action='store_true',
        help='Overwrite the local file if it already exists.',
    )

  def Run(self, args):
    """Run the download command."""
    revision_ref = args.CONCEPTS.revision.Parse()

    destination = os.path.expanduser(args.destination)
    if os.path.isdir(destination):
      filename = '{}.zip'.format(revision_ref.revisionsId)
      final_path = os.path.join(destination, filename)
    else:
      filename = os.path.basename(destination)
      final_path = destination

    dest_dir = os.path.dirname(final_path)
    if dest_dir and not os.path.exists(dest_dir):
      raise core_exceptions.Error(
          'Destination directory does not exist: {}'.format(dest_dir)
      )

    if os.path.exists(final_path) and not args.allow_overwrite:
      raise core_exceptions.Error(
          'File already exists: {}. Use --allow-overwrite to replace it.'
          .format(final_path)
      )

    default_chunk_size = 3 * 1024 * 1024
    download_util.Download(
        dest_path=final_path,
        revision_res_name=revision_ref.RelativeName(),
        file_name=filename,
        allow_overwrite=args.allow_overwrite,
        chunk_size=default_chunk_size,
        parallelism=1,  # Can add --parallelism flag later if needed
    )

    if zipfile.is_zipfile(final_path):
      extract_dir = (
          final_path[:-4]
          if final_path.lower().endswith('.zip')
          else final_path + '_extracted'
      )
      with zipfile.ZipFile(final_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
      log.status.Print(
          'Successfully downloaded and extracted revision payload to {}'.format(
              extract_dir
          )
      )
      # Clean up the raw zip file now that it's extracted
      os.remove(final_path)
    else:
      log.status.Print(
          'Successfully downloaded revision payload to {}'.format(final_path)
      )
