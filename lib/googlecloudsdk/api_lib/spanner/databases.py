# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Spanner database API helper."""

from typing import Any

from apitools.base.py import list_pager
from cloudsdk.google.protobuf import descriptor_pb2
from cloudsdk.google.protobuf import text_format
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.spanner.resource_args import CloudKmsKeyName
from googlecloudsdk.core import resources

# The list of pre-defined IAM roles in Spanner.
KNOWN_ROLES = [
    'roles/spanner.admin', 'roles/spanner.databaseAdmin',
    'roles/spanner.databaseReader', 'roles/spanner.databaseUser',
    'roles/spanner.viewer'
]

# The available options of the SQL dialect for a Cloud Spanner database.
DATABASE_DIALECT_GOOGLESQL = 'GOOGLE_STANDARD_SQL'
DATABASE_DIALECT_POSTGRESQL = 'POSTGRESQL'


def Create(
    instance_ref,
    database,
    ddl,
    proto_descriptors=None,
    kms_key: CloudKmsKeyName = None,
    database_dialect=None,
):
  """Create a new database."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req_args = {
      'createStatement': 'CREATE DATABASE `{}`'.format(database),
      'extraStatements': ddl,
  }
  if proto_descriptors:
    req_args['protoDescriptors'] = proto_descriptors
  if database_dialect:
    database_dialect = database_dialect.upper()
    if database_dialect == DATABASE_DIALECT_POSTGRESQL:
      req_args['createStatement'] = 'CREATE DATABASE "{}"'.format(database)
      req_args[
          'databaseDialect'] = msgs.CreateDatabaseRequest.DatabaseDialectValueValuesEnum.POSTGRESQL
    else:
      req_args[
          'databaseDialect'] = msgs.CreateDatabaseRequest.DatabaseDialectValueValuesEnum.GOOGLE_STANDARD_SQL
  if kms_key:
    req_args['encryptionConfig'] = msgs.EncryptionConfig(
        kmsKeyName=kms_key.kms_key_name, kmsKeyNames=kms_key.kms_key_names
    )
  req = msgs.SpannerProjectsInstancesDatabasesCreateRequest(
      parent=instance_ref.RelativeName(),
      createDatabaseRequest=msgs.CreateDatabaseRequest(**req_args))
  return client.projects_instances_databases.Create(req)


def SetPolicy(database_ref, policy):
  """Saves the given policy on the database, overwriting whatever exists."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
  req = msgs.SpannerProjectsInstancesDatabasesSetIamPolicyRequest(
      resource=database_ref.RelativeName(),
      setIamPolicyRequest=msgs.SetIamPolicyRequest(policy=policy))
  return client.projects_instances_databases.SetIamPolicy(req)


def Delete(database_ref):
  """Delete a database."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesDropDatabaseRequest(
      database=database_ref.RelativeName())
  return client.projects_instances_databases.DropDatabase(req)


def GetIamPolicy(database_ref):
  """Gets the IAM policy on a database."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesGetIamPolicyRequest(
      getIamPolicyRequest=msgs.GetIamPolicyRequest(
          options=msgs.GetPolicyOptions(
              requestedPolicyVersion=
              iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
      resource=database_ref.RelativeName())
  return client.projects_instances_databases.GetIamPolicy(req)


def Get(database_ref):
  """Get a database by name."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesGetRequest(
      name=database_ref.RelativeName())
  return client.projects_instances_databases.Get(req)


def GetDdl(database_ref):
  """Get a database's DDL description."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesGetDdlRequest(
      database=database_ref.RelativeName())
  return client.projects_instances_databases.GetDdl(req).statements


def GetDdlWithDescriptors(database_ref, args):
  """Get a database's DDL description."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesGetDdlRequest(
      database=database_ref.RelativeName()
  )
  get_ddl_resp = client.projects_instances_databases.GetDdl(req)
  if not args.include_proto_descriptors:
    return get_ddl_resp.statements

  ddls = ';\n\n'.join(get_ddl_resp.statements) + ';\n\n'
  descriptors = descriptor_pb2.FileDescriptorSet.FromString(
      get_ddl_resp.protoDescriptors
  )
  return (
      ddls
      + 'Proto Bundle Descriptors:\n'
      + text_format.MessageToString(descriptors)
  )


def List(instance_ref):
  """List databases in the instance."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesListRequest(
      parent=instance_ref.RelativeName())
  return list_pager.YieldFromList(
      client.projects_instances_databases,
      req,
      field='databases',
      batch_size_attribute='pageSize')


def UpdateDdl(database_ref, ddl, proto_descriptors=None):
  """Update a database via DDL commands."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  update_ddl_req = msgs.UpdateDatabaseDdlRequest(statements=ddl)
  if proto_descriptors:
    update_ddl_req.protoDescriptors = proto_descriptors
  req = msgs.SpannerProjectsInstancesDatabasesUpdateDdlRequest(
      database=database_ref.RelativeName(),
      updateDatabaseDdlRequest=update_ddl_req)
  return client.projects_instances_databases.UpdateDdl(req)


def Restore(database_ref, backup_ref, encryption_type=None, kms_key=None):
  """Restore a database from a backup."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')

  restore_db_request = msgs.RestoreDatabaseRequest(
      backup=backup_ref.RelativeName(), databaseId=database_ref.Name())
  if kms_key:
    restore_db_request.encryptionConfig = msgs.RestoreDatabaseEncryptionConfig(
        encryptionType=encryption_type,
        kmsKeyName=kms_key.kms_key_name,
        kmsKeyNames=kms_key.kms_key_names,
    )
  elif encryption_type:
    restore_db_request.encryptionConfig = msgs.RestoreDatabaseEncryptionConfig(
        encryptionType=encryption_type,
    )

  req = msgs.SpannerProjectsInstancesDatabasesRestoreRequest(
      parent=database_ref.Parent().RelativeName(),
      restoreDatabaseRequest=restore_db_request)
  return client.projects_instances_databases.Restore(req)


def Update(
    database_ref: resources.Resource,
    enable_drop_protection: bool | None = None,
    kms_keys: list[str] | None = None,
    clear_kms_keys: bool = False,
) -> Any:
  """Update a database.

  Args:
    database_ref: The reference to the database to update.
    enable_drop_protection: Whether to enable drop protection on the database.
    kms_keys: The list of KMS key names to be used to encrypt the database.
    clear_kms_keys: Whether to clear KMS key references and revert to
      Google-managed encryption.

  Returns:
    The long-running operation for the database update.

  Raises:
    errors.NoFieldsSpecifiedError: If no updates or multiple updates are
    requested.
  """
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')

  flags_set = [
      enable_drop_protection is not None,
      kms_keys is not None,
      clear_kms_keys,
  ].count(True)
  if flags_set == 0:
    raise errors.NoFieldsSpecifiedError(
        'No updates requested. Need to specify at least one of '
        '--[no-]enable-drop-protection, --kms-keys, or --clear-kms-keys.'
    )
  if flags_set > 1:
    raise errors.NoFieldsSpecifiedError(
        'Multiple updates requested. Please specify only one flag.'
    )

  if enable_drop_protection is not None:
    database_obj = msgs.Database(
        name=database_ref.RelativeName(),
        enableDropProtection=enable_drop_protection,
    )
    update_mask = ['enable_drop_protection']
  elif kms_keys is not None:
    database_obj = msgs.Database(
        name=database_ref.RelativeName(),
        encryptionConfig=msgs.EncryptionConfig(kmsKeyNames=kms_keys),
    )
    update_mask = ['encryption_config']
  elif clear_kms_keys:
    database_obj = msgs.Database(name=database_ref.RelativeName())
    update_mask = ['encryption_config']

  req = msgs.SpannerProjectsInstancesDatabasesPatchRequest(
      database=database_obj,
      name=database_ref.RelativeName(),
      updateMask=','.join(update_mask),
  )

  cleared_fields = ['encryptionConfig'] if clear_kms_keys else []
  with client.IncludeFields(cleared_fields):
    return client.projects_instances_databases.Patch(req)


def ChangeQuorum(database_ref, quorum_type, etag=None):
  """ChangeQuorum a database."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')

  req = msgs.ChangeQuorumRequest(
      etag=etag, name=database_ref.RelativeName(), quorumType=quorum_type
  )
  return client.projects_instances_databases.Changequorum(req)
