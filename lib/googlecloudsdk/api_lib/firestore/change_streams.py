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
"""Useful commands for interacting with the Cloud Firestore ChangeStreams API."""

from googlecloudsdk.api_lib.firestore import api_utils


def _GetChangeStreamService():
  """Returns the service for interacting with the Firestore change streams service."""
  return api_utils.GetClient().projects_databases_changeStreams


def CreateChangeStream(
    project,
    database,
    change_stream_id,
    retention_period=None,
    database_scope=False,
    collection_group_id=None,
):
  """Performs a Firestore Admin v1 ChangeStream Creation.

  Args:
    project: the project id to create, a string.
    database: the database id to create, a string.
    change_stream_id: the change stream id to create, a string.
    retention_period: the retention period, a string (e.g. '86400s'), or None.
    database_scope: whether the stream is database scoped, a boolean.
    collection_group_id: the collection group id if collection group scoped, a
      string, or None.

  Returns:
    a ChangeStream resource.
  """
  if not database_scope and not collection_group_id:
    raise ValueError(
        'The change stream must be either database-scoped or collection-group'
        '-scoped'
    )

  messages = api_utils.GetMessages()
  change_stream = messages.GoogleFirestoreAdminV1ChangeStream()
  if retention_period:
    change_stream.retentionPeriod = retention_period
  if database_scope:
    change_stream.databaseScope = messages.GoogleFirestoreAdminV1DatabaseScope()
  elif collection_group_id:
    change_stream.collectionGroupScope = (
        messages.GoogleFirestoreAdminV1CollectionGroupScope(
            collectionGroupId=collection_group_id
        )
    )

  return _GetChangeStreamService().Create(
      messages.FirestoreProjectsDatabasesChangeStreamsCreateRequest(
          parent='projects/{}/databases/{}'.format(project, database),
          changeStreamId=change_stream_id,
          googleFirestoreAdminV1ChangeStream=change_stream,
      )
  )
