# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""The gcloud datastore indexes cleanup command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.datastore import constants
from googlecloudsdk.api_lib.datastore import index_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.app import output_helpers
from googlecloudsdk.command_lib.datastore import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Cleanup(base.Command):
  """Cleanup Cloud Datastore indexes."""

  detailed_help = {
      'brief': (
          'Remove unused datastore indexes based on your local index '
          'configuration.'
      ),
      'DESCRIPTION': """
This command removes unused datastore indexes based on your local index
configuration. Any indexes that exist that are not in the index file will be
removed.
      """,
      'EXAMPLES': """\
          To remove unused indexes based on your local configuration, run:

            $ {command} ~/myapp/index.yaml
          """,
  }

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    """Get arguments for this command."""
    flags.AddIndexFileFlag(parser)

  def Run(self, args) -> None:
    self.Cleanup(args.index_file, use_firestore_admin=False)

  def Cleanup(
      self, index_file: str, database=None, use_firestore_admin=False
  ) -> None:
    project = properties.VALUES.core.project.Get(required=True)
    info = yaml_parsing.ConfigYamlInfo.FromFile(index_file)
    if not info or info.name != yaml_parsing.ConfigYamlInfo.INDEX:
      raise exceptions.InvalidArgumentException(
          'index_file', 'You must provide the path to a valid index.yaml file.'
      )
    output_helpers.DisplayProposedConfigDeployments(
        project=project, configs=[info]
    )
    console_io.PromptContinue(
        default=True, throw_if_unattended=False, cancel_on_no=True
    )
    if use_firestore_admin:
      self.PerformApiCleanupViaFirestoreAdmin(info, project, database)
    else:
      self.PerformApiCleanupViaDatastoreAdmin(info, project)

  def PerformApiCleanupViaDatastoreAdmin(
      self, info: yaml_parsing.ConfigYamlInfo, project: str
  ) -> None:
    received_indexes = index_api.NormalizeIndexes(info.parsed.indexes or [])
    indexes_to_delete_ids = set()
    current_indexes = index_api.ListIndexes(project)
    for index_id, index in current_indexes:
      if index in received_indexes:
        continue
      msg = (
          'This index is no longer defined in your index.yaml file.\n{0}'
          .format(index.ToYAML())
      )
      prompt = 'Do you want to delete this index'
      if console_io.PromptContinue(msg, prompt, default=True):
        indexes_to_delete_ids.add(index_id)
    index_api.DeleteIndexes(project, indexes_to_delete_ids)

  def PerformApiCleanupViaFirestoreAdmin(
      self, info: yaml_parsing.ConfigYamlInfo, project: str, database: str
  ) -> None:
    received_indexes = index_api.NormalizeIndexes(info.parsed.indexes or [])
    indexes_to_delete_ids = set()
    current_indexes = index_api.ListDatastoreIndexesViaFirestoreApi(
        project, database
    )
    for index_id, index in current_indexes:
      # Firestore API returns index with '__name__' field path. Normalizing the
      # index is required.
      normalized_index = index_api.NormalizeIndex(index)
      if normalized_index in received_indexes:
        continue
      msg = (
          'This index is no longer defined in your index.yaml file.\n{0}'
          .format(index.ToYAML())
      )
      prompt = 'Do you want to delete this index'
      if console_io.PromptContinue(msg, prompt, default=True):
        indexes_to_delete_ids.add(index_id)
    index_api.DeleteIndexesViaFirestoreApi(
        project, database, indexes_to_delete_ids
    )


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CleanupFirestoreApi(Cleanup):
  """Create Cloud Datastore indexes with Firestore API."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    """Get arguments for this command.

    Args:
      parser: argparse.ArgumentParser, the parser for this command.
    """
    flags.AddIndexFileFlag(parser)
    parser.add_argument(
        '--database',
        help="""\
        The database to operate on. If not specified, the CLI refers the
        `(default)` database by default.

        For example, to operate on database `testdb`:

          $ {command} --database='testdb'
        """,
        type=str,
    )

  def Run(self, args) -> None:
    # Default to '(default)' if unset.
    database_id = (
        constants.DEFAULT_NAMESPACE if not args.database else args.database
    )
    self.Cleanup(
        index_file=args.index_file,
        database=database_id,
        use_firestore_admin=True,
    )
