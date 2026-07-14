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
"""Command to create a Cloud Firestore composite index."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.firestore import api_utils as fs_api_utils
from googlecloudsdk.api_lib.firestore import indexes as indexes_api
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.firestore import flags as firestore_flags
from googlecloudsdk.command_lib.firestore import index_create_cli_to_message_converter as index_create_utils
from googlecloudsdk.command_lib.firestore import resource_args
from googlecloudsdk.command_lib.firestore import util as firestore_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import text


class _OperationPoller(waiter.CloudOperationPollerNoResources):
  """Default Poller class returns operation.response in GetResult().

  We need the full operation object in order to extract the index id from
  operation.metadata.
  """

  def GetResult(self, op):
    return op


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Create a new composite index."""

  detailed_help = {
      'DESCRIPTION': 'Create a new composite index.',
      'EXAMPLES': (
          """\
          The following command creates a composite index with fields ``user_id'' (in descending order)
          followed by ``timestamp'' (in descending order) in the ``Events'' collection group.

            $ {command} --collection-group=Events \\
                --field-config=field-path=user-id,order=descending \\
                --field-config=field-path=timestamp,order=descending

            $ {command} --database=(default) --collection-group=Events \\
                --field-config=field-path=user-id,order=descending \\
                --field-config=field-path=timestamp,order=descending
          """
      ),
      'API REFERENCE': (
          """\
          This command uses the firestore/v1 API.

          The index specification can be found at:
          https://firebase.google.com/docs/firestore/reference/rpc/google.firestore.admin.v1#index_1

          The full API documentation can be found at:
          https://cloud.google.com/firestore
          """
      ),
  }

  @classmethod
  def Args(cls, parser):
    is_search_released = cls._IsSearchReleased()

    resource_args.AddCollectionGroupResourceArg(parser)
    firestore_flags.AddFieldConfigFlag(parser, is_search_released)
    firestore_flags.AddQueryScopeFlag(parser)
    firestore_flags.AddApiScopeFlag(parser)
    firestore_flags.AddDensityFlag(parser)
    firestore_flags.AddMultikeyFlag(parser)
    firestore_flags.AddUniqueFlag(parser)
    firestore_flags.AddSearchIndexOptionsFlag(parser, is_search_released)
    base.ASYNC_FLAG.AddToParser(parser)

    # Silences the default terminal output
    parser.display_info.AddFormat('none')

  def Run(self, args):
    ref = args.CONCEPTS.collection_group.Parse()
    project = ref.projectsId
    database = ref.databasesId
    collection_group = ref.collectionGroupsId

    search_index_options = (
        args.search_index_options if self._IsSearchReleased() else None
    )

    index_message = index_create_utils.BuildIndexMessage(
        field_configs=args.field_config,
        query_scope=args.query_scope,
        api_scope=args.api_scope,
        multikey=args.multikey,
        density=args.density,
        unique=args.unique,
        search_index_options=search_index_options,
    )

    self._ValidateIndexMessage(index_message)

    try:
      operation = indexes_api.CreateIndex(
          project, database, collection_group, index_message
      )
    except apitools_exceptions.HttpError as e:
      raise api_exceptions.HttpException(e) from e
    log.status.Print('Create request issued')

    if args.async_:
      log.status.Print(f'Check operation [{operation.name}] for status.')
      return operation

    return self._WaitForIndex(operation)

  @classmethod
  def _IsSearchReleased(cls):
    """Returns whether search indexes are released for this release track."""
    return cls.ReleaseTrack() in (
        base.ReleaseTrack.ALPHA,
        base.ReleaseTrack.BETA,
    )

  def _ValidateIndexMessage(self, index_message):
    """Validates the index message."""

    field_configs = index_message.fields
    self._ValidateFieldConfig(field_configs)

  def _ValidateFieldConfig(self, field_configs):
    """Validates the combination of field configuration types."""
    invalid_field_configs = []
    for field_config in field_configs:
      configs = [
          field_config.order,
          field_config.arrayConfig,
          field_config.vectorConfig,
          field_config.searchConfig,
      ]
      populated_configs = [config for config in configs if config is not None]

      if len(populated_configs) != 1:
        invalid_field_configs.append(field_config)

    if invalid_field_configs:
      if self.ReleaseTrack() == base.ReleaseTrack.GA:
        error_msg = (
            "Exactly one of 'order', 'array-config', or 'vector-config' must be"
        )
      else:
        error_msg = (
            "Exactly one of 'order', 'array-config', 'vector-config', or"
            " 'search-config' must be"
        )

      error_msg += (
          ' specified for the {field_word} with the following {path_word}:'
          ' [{paths}].'.format(
              field_word=text.Pluralize(len(invalid_field_configs), 'field'),
              path_word=text.Pluralize(len(invalid_field_configs), 'path'),
              paths=', '.join(
                  field_config.fieldPath
                  for field_config in invalid_field_configs
              ),
          )
      )
      raise calliope_exceptions.InvalidArgumentException(
          '--field-config', error_msg
      )

  def _WaitForIndex(self, operation):
    """Polls for operation completion and prints progress logs."""

    poller = _OperationPoller(
        fs_api_utils.GetClient().projects_databases_operations,
        get_name_func=lambda x: x.RelativeName(),
    )

    operation_ref = resources.REGISTRY.Parse(
        operation.name,
        collection='firestore.projects.databases.operations',
        api_version=fs_api_utils.FIRESTORE_API_VERSION,
    )

    completed_operation = waiter.WaitFor(
        poller,
        operation_ref,
        f'Waiting for operation [{operation_ref.RelativeName()}] to complete',
    )

    metadata = firestore_util.ExtractOperationMetadata(
        completed_operation, None
    )
    index_id = metadata.index.split('/')[-1]
    log.CreatedResource(index_id, kind='index')

    return completed_operation
