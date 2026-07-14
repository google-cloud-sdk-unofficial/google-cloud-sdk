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

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import arg_parsers


def AddDescriptionArg(parser):
  """Adds argument for description."""
  parser.add_argument(
      '--description',
      help='Description of the resource.',
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
  AddDescriptionArg(parser)
  AddRestrictedLocationsArg(parser)
  AddDefaultLocationArg(parser)


def AddServiceDirectoryNameArg(parser):
  """Adds argument for service directory name."""
  parser.add_argument(
      '--service-directory-name',
      help=(
          'The service directory resource name for request routing, in the'
          ' format'
          ' `projects/{project_id}/locations/{location}/namespaces/{namespace}/services/{service_name}`.'
          ' see https://docs.cloud.google.com/lakehouse/docs/set-up-cross-cloud-lakehouse#setup-cci.'
      ),
  )


def AddUnityServicePrincipalApplicationIdArg(parser):
  """Adds argument for service principal application ID."""
  parser.add_argument(
      '--unity-service-principal-application-id',
      help=(
          'Optional. The application ID of the Databricks service principal'
          ' that will be used to access the Unity Catalog in the OIDC'
          ' authentication flow. With OIDC, the secret-name argument is not'
          ' used.'
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


def AddFederatedCatalogArgs(
    parser, support_snowflake=False, support_workday=False
):
  """Adds arguments for federated catalogs."""
  choices = ['unity', 'glue']
  hidden_choices = []
  if support_snowflake:
    choices.append('snowflake')
    hidden_choices.append('snowflake')
  if support_workday:
    choices.append('workday')
    hidden_choices.append('workday')

  parser.add_argument(
      '--federated-catalog-type',
      choices=choices,
      hidden_choices=hidden_choices,
      help='Type of the federated catalog.',
  )
  parser.add_argument(
      '--secret-name',
      help=(
          'The secret resource name in Secret Manager, in the format'
          ' `projects/{project_id}/locations/{location}/secrets/{secret_id}`'
          ' or `projects/{project_id}/locations/{location}/secrets/{secret_id}/'
          'versions/{version_id}`.'
      ),
  )

  parser.add_argument(
      '--unity-catalog-name',
      help='Name of the catalog in Unity Catalog.',
  )
  parser.add_argument(
      '--unity-instance-name',
      help=(
          'The instance name is the first part of the URL when you log into'
          ' your Databricks deployment. For example, for a Databricks on'
          ' Google Cloud workspace URL https://1.1.gcp.databricks.com, the'
          ' instance name is 1.1.gcp.databricks.com.'
      ),
  )
  parser.add_argument(
      '--refresh-interval',
      type=arg_parsers.Duration(),
      help=(
          'The interval for refreshing metadata from the remote catalog (e.g.,'
          ' "1hr5m30s"). Defaults to seconds if no unit is specified. If unset,'
          ' the refresh interval will be set to 0s (background refresh'
          ' disabled).'
      ),
  )
  parser.add_argument(
      '--namespace-filters',
      type=arg_parsers.ArgList(),
      metavar='NAMESPACE',
      help=(
          'Filters to determine which namespaces are included in the refresh'
          ' process. Empty list means include all namespaces.'
      ),
  )


def AddGlueCatalogArgs(parser):
  """Adds arguments for Glue catalogs."""
  parser.add_argument(
      '--glue-warehouse',
      help='The warehouse to connect to in AWS Glue Iceberg REST Catalog.',
  )
  parser.add_argument(
      '--glue-aws-region',
      help='The AWS region of the Glue catalog to connect to.',
  )
  AddGlueAwsRoleArnArg(parser)


def AddUpdateFederatedCatalogArgs(parser):
  """Adds arguments for updating federated catalogs."""
  parser.add_argument(
      '--secret-name',
      help=(
          'Resource name of the Secret Manager secret, in the format'
          ' `projects/{project_id}/locations/{location}/secrets/{secret_id}`'
          ' or `projects/{project_id}/locations/{location}/secrets/{secret_id}/'
          'versions/{version_id}`.'
      ),
  )

  parser.add_argument(
      '--refresh-interval',
      type=arg_parsers.Duration(),
      help=(
          'Interval for refreshing metadata from the remote catalog (e.g.,'
          ' "1hr5m30s"). Defaults to seconds if no unit is specified. If unset,'
          ' the refresh interval will be set to 0s (background refresh'
          ' disabled).'
      ),
  )
  parser.add_argument(
      '--namespace-filters',
      type=arg_parsers.ArgList(),
      metavar='NAMESPACE',
      help=(
          'Filters to determine which namespaces are included in the refresh'
          ' process. Empty list means include all namespaces.'
      ),
  )


def AddDefaultLocationArg(parser):
  """Adds argument for default location. Used for BigLake catalogs."""
  parser.add_argument(
      '--default-location',
      type=util.GcsBucketLinkValidator,
      help=(
          'Can only be used with BigLake catalogs. The default'
          ' storage location for the catalog, e.g., `gs://my-bucket/...`.'
      ),
  )


def AddRestrictedLocationsArg(parser):
  """Adds argument for restricted locations. Used for BigLake catalogs."""
  parser.add_argument(
      '--restricted-locations',
      type=arg_parsers.ArgList(element_type=util.GcsBucketLinkValidator),
      metavar='LOCATION',
      help=(
          'Additional Google Cloud Storage buckets and locations (e.g.,'
          ' `gs://my-other-bucket/...`) that are permitted for use by'
          ' resources within a catalog. This field is currently only used'
          ' for BigLake catalogs.'
          'If `restricted_locations` is empty and unrestricted catalog'
          ' creation is enabled, all accessible locations are allowed.'
          ' Otherwise, only `default_location` and locations in this'
          ' list are allowed.'
      ),
  )


def AddGlueAwsRoleArnArg(parser):
  """Adds Glue AWS role ARN argument."""
  parser.add_argument(
      '--glue-aws-role-arn',
      help=(
          'The AWS role ARN of the Glue catalog that the BigLake federated'
          ' catalog will assume to access the catalog.'
      ),
  )


def AddSnowflakeCatalogArgs(parser):
  """Adds arguments for Snowflake catalogs."""
  parser.add_argument(
      '--snowflake-warehouse',
      hidden=True,
      help='The warehouse to connect to in Snowflake.',
  )
  parser.add_argument(
      '--snowflake-account-identifier',
      hidden=True,
      help='The account identifier of the Snowflake catalog to connect to.',
  )


def AddWorkdayCatalogArgs(parser):
  """Adds arguments for Workday catalogs."""
  parser.add_argument(
      '--workday-base-url',
      hidden=True,
      help='The base URL of the Workday instance.',
  )
  parser.add_argument(
      '--workday-tenant',
      hidden=True,
      help='The Workday tenant name.',
  )


def AddHiveTableCreateArgs(parser):
  """Adds arguments for creating Hive tables."""
  parser.add_argument(
      '--file',
      required=True,
      help=(
          'Path to a JSON or YAML file containing the Hive table definition.'
          ' The format must follow the Hive Metastore API specification for'
          ' `HiveTable`. The field `storageDescriptor` must be specified.'
      ),
  )
