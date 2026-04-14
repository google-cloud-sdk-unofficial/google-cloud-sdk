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

"""Defines arguments for BigLake commands."""

from googlecloudsdk.calliope import arg_parsers

# TODO(b/461544141): Move methods that define commands arguments from util.py
# to this file.


def AddDescriptionArg(parser):
  """Adds argument for description."""
  parser.add_argument(
      '--description',
      help='Description of the resource being created.',
  )


def AddPropertiesArg(parser):
  """Adds argument for creating properties."""
  parser.add_argument(
      '--properties',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=(
          'Properties associated with the namespace.'
      ),
  )


def AddUpdatePropertiesArgs(parser):
  """Adds arguments for updating properties."""
  parser.add_argument(
      '--update-properties',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=(
          'List of properties to update or add.'
      ),
  )
  parser.add_argument(
      '--remove-properties',
      metavar='KEY',
      type=arg_parsers.ArgList(),
      help=(
          'List of properties to remove.'
      ),
  )
  parser.add_argument(
      '--clear-properties',
      action='store_true',
      default=False,
      help=(
          'Clear all properties from the namespace.'
      ),
  )


def AddTableDescribeArgs(parser):
  """Adds arguments for describing tables."""
  parser.add_argument(
      '--snapshots',
      help='Snapshot to get.',
  )


def AddTableRegisterArgs(parser):
  """Adds arguments for registering tables."""
  parser.add_argument(
      '--metadata-location',
      required=True,
      help='Metadata location of the table.',
  )
  parser.add_argument(
      '--overwrite',
      action='store_true',
      default=False,
      help='Overwrite the table if it already exists.',
  )


def AddCatalogsCreateArgs(parser):
  """Adds arguments for creating catalogs."""
  parser.add_argument(
      '--primary-location',
      help=(
          'Primary location for mirroring the remote catalog metadata. It'
          ' must be a BigLake-supported location, and it should be proximate to'
          ' the remote catalog\'s location for better performance and lower'
          ' cost.'
      ),
  )


def AddServiceDirectoryNameArg(parser):
  """Adds argument for service directory name."""
  parser.add_argument(
      '--service-directory-name',
      hidden=True,
      help=(
          'The service directory resource name for request routing. See'
          ' cross-cloud interconnect documentation for more details.'
      ),
  )


def AddTableCreateArgs(parser):
  """Adds arguments for creating tables."""
  parser.add_argument(
      '--create-from-file',
      required=True,
      help=(
          'Path to a JSON file containing the table creation request. The'
          ' format must follow the Apache Iceberg REST Catalog Open API'
          ' specification for `CreateTableRequest`. The fields `name` and'
          ' `schema` must be specified.'
      ),
  )


def AddFederatedCatalogArgs(parser):
  """Adds arguments for federated catalogs."""
  parser.add_argument(
      '--federated-catalog-type',
      hidden=True,
      choices=['unity'],
      help='Type of the federated catalog.',
  )
  parser.add_argument(
      '--secret-name',
      hidden=True,
      help=(
          'The secret resource name in Secret Manager, in the format'
          ' `projects/{project_id}/locations/{location}/secrets/{secret_id}`'
          ' or `projects/{project_id}/locations/{location}/secrets/{secret_id}/'
          'versions/{version_id}`.'
      ),
  )
  parser.add_argument(
      '--unity-instance-name',
      hidden=True,
      help=(
          'The instance name is the first part of the URL when you log into'
          ' your Databricks deployment. For example, for a Databricks on GCP'
          ' workspace URL https://1.1.gcp.databricks.com, the instance name is'
          ' 1.1.gcp.databricks.com.'
      ),
  )
  parser.add_argument(
      '--unity-catalog-name',
      hidden=True,
      help='Name of the catalog in Unity Catalog.',
  )
  parser.add_argument(
      '--refresh-interval',
      hidden=True,
      type=arg_parsers.Duration(),
      help=(
          'The interval for refreshing metadata from the remote catalog (e.g.,'
          ' "1hr5m30s"). Defaults to seconds if no unit is specified.'
      ),
  )
  parser.add_argument(
      '--namespace-filters',
      hidden=True,
      type=arg_parsers.ArgList(),
      metavar='NAMESPACE',
      help=(
          'Filters to determine which namespaces are included in the refresh'
          ' process. - empty list means include all namespaces. -'
          ' "[namespaces]" means include the specified namespaces.'
      ),
  )


def AddUpdateFederatedCatalogArgs(parser):
  """Adds arguments for updating federated catalogs."""
  parser.add_argument(
      '--secret-name',
      hidden=True,
      help=(
          'Resource name of the Secret Manager secret, in the format'
          ' `projects/{project_id}/locations/{location}/secrets/{secret_id}`'
          ' or `projects/{project_id}/locations/{location}/secrets/{secret_id}/'
          'versions/{version_id}`.'
      ),
  )
  parser.add_argument(
      '--refresh-interval',
      hidden=True,
      type=arg_parsers.Duration(),
      help=(
          'Interval for refreshing metadata from the remote catalog (e.g.,'
          ' "1hr5m30s"). Defaults to seconds if no unit is specified.'
      ),
  )
  parser.add_argument(
      '--namespace-filters',
      hidden=True,
      type=arg_parsers.ArgList(),
      metavar='NAMESPACE',
      help=(
          'Filters to determine which namespaces are included in the refresh'
          ' process. - empty list means include all namespaces. -'
          ' "[namespaces]" means include the specified namespaces.'
      ),
  )
