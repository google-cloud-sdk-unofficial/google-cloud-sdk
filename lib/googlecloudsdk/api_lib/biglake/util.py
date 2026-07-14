# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""A library that is used to support our commands."""

import json
import types
from typing import Any, Dict
from urllib import parse

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.credentials import requests
from six.moves import http_client as httplib


quote_plus = parse.quote_plus
VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1',
    base.ReleaseTrack.BETA: 'v1',
    base.ReleaseTrack.GA: 'v1',
}


class HttpRequestFailError(core_exceptions.Error):
  """Indicates that the http request fails in some way."""

  pass


# The messages module can also be accessed from client.MESSAGES_MODULE
def GetMessagesModule(release_track=base.ReleaseTrack.ALPHA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetMessagesModule('biglake', api_version)


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance('biglake', api_version)


def GetCatalogRef(catalog):
  """Get a resource reference to a catalog."""
  return resources.REGISTRY.Parse(
      catalog,  # in the format of projects/{project-id}/catalogs/{catalog-id}
      params={
          'projectsId': properties.VALUES.core.project.GetOrFail,
      },
      collection='biglake.iceberg.v1.restcatalog.extensions.projects.catalogs',
  )


def GetNamespaceName(catalog_id, namespace_id):
  """Get the namespace name.

  The name is in the format of
  projects/{project-id}/catalogs/{catalog-id}/namespaces/{namespace-id}.

  Args:
    catalog_id: The ID of the catalog.
    namespace_id: The ID of the namespace.

  Returns:
    The namespace name string.
  """
  return f'projects/{properties.VALUES.core.project.GetOrFail()}/catalogs/{catalog_id}/namespaces/{namespace_id}'


def GetCatalogName(catalog_id):
  """Get the catalog name.

  The name is in the format of projects/{project-id}/catalogs/{catalog-id}.

  Args:
    catalog_id: The ID of the catalog.

  Returns:
    The catalog name string.
  """
  return f'projects/{properties.VALUES.core.project.GetOrFail()}/catalogs/{catalog_id}'


def GetTableName(catalog_id, namespace_id, table_id):
  """Get the table name.

  The name is in the format of
  projects/{project-id}/catalogs/{catalog-id}/namespaces/{namespace-id}/tables/{table-id}.

  Args:
    catalog_id: The ID of the catalog.
    namespace_id: The ID of the namespace.
    table_id: The ID of the table.

  Returns:
    The table name string.
  """
  return f'projects/{properties.VALUES.core.project.GetOrFail()}/catalogs/{catalog_id}/namespaces/{namespace_id}/tables/{table_id}'


def GetParentName():
  """Get the parent name in the format of projects/{project-id}."""
  return f'projects/{properties.VALUES.core.project.GetOrFail()}'


def GetCatalogTypeEnumMapper(release_track):
  messages = GetMessagesModule(release_track)
  catalog_type_enum = messages.IcebergCatalog.CatalogTypeValueValuesEnum
  return arg_utils.ChoiceEnumMapper(
      '--catalog-type',
      catalog_type_enum,
      hidden_choices=['federated']
      if release_track == base.ReleaseTrack.GA
      else [],
      required=True,
      help_str='Catalog type to create the catalog with.',
      custom_mappings={
          'CATALOG_TYPE_GCS_BUCKET': (
              'gcs-bucket',
              'A catalog backed by a Cloud Storage bucket.',
          ),
          'CATALOG_TYPE_BIGLAKE': (
              'biglake',
              (
                  'BigLake Iceberg catalog. Catalog type which allows'
                  ' namespaces and tables within a catalog to be mapped to'
                  " locations beyond the catalog's designated default."
              ),
          ),
          'CATALOG_TYPE_FEDERATED': (
              'federated',
              'BigLake federated catalog mirroring a remote catalog.',
          ),
      },
  )


def GetUpdateCatalogTypeEnumMapper(release_track):
  messages = GetMessagesModule(release_track)
  catalog_type_enum = messages.IcebergCatalog.CatalogTypeValueValuesEnum
  return arg_utils.ChoiceEnumMapper(
      '--catalog-type',
      catalog_type_enum,
      required=False,
      help_str=(
          'Catalog type to update the catalog with. Currently only updating to '
          'a BigLake catalog type is supported.'
      ),
      custom_mappings={
          'CATALOG_TYPE_BIGLAKE': (
              'biglake',
              (
                  'BigLake Iceberg catalog. Catalog type which allows'
                  ' namespaces and tables within a catalog to be mapped to'
                  " locations beyond the catalog's designated default."
              ),
          ),
      },
  )


def GetCredentialModeEnumMapper(release_track):
  messages = GetMessagesModule(release_track)
  credential_mode_enum = messages.IcebergCatalog.CredentialModeValueValuesEnum
  return arg_utils.ChoiceEnumMapper(
      '--credential-mode',
      credential_mode_enum,
      default='end-user',
      help_str='Credential mode to create the catalog with.',
      custom_mappings={
          'CREDENTIAL_MODE_END_USER': (
              'end-user',
              'Use end user credentials to access the catalog.',
          ),
          'CREDENTIAL_MODE_VENDED_CREDENTIALS': (
              'vended-credentials',
              'Use vended credentials to access the catalog.',
          ),
      },
  )


def GcsBucketLinkValidator(value):
  if not value.startswith('gs://'):
    raise arg_parsers.ArgumentTypeError(
        'Location must be a Google Cloud Storage URI starting with `gs://`'
    )
  return value


def CheckValidArgCombinations(args):
  """Checks for valid combinations of arguments.

  Ensures that `--default-location` and `--restricted-locations`
  are only used when `--catalog-type` is 'BigLake'.

  Args:
    args: The parsed command-line arguments.

  Raises:
    arg_parsers.ArgumentTypeError: If an invalid argument combination is found.
  """
  if args.catalog_type == 'biglake' and not args.IsSpecified(
      'default_location'
  ):
    raise arg_parsers.ArgumentTypeError(
        '--default-location must be specified when catalog type is BigLake.'
    )
  elif args.catalog_type != 'biglake' and args.IsSpecified('default_location'):
    raise arg_parsers.ArgumentTypeError(
        '--default-location is only supported for BigLake catalogs.'
    )
  elif args.catalog_type != 'biglake' and args.IsSpecified(
      'restricted_locations'
  ):
    raise arg_parsers.ArgumentTypeError(
        '--restricted-locations is only supported for BigLake catalogs.'
    )


def CheckValidUnityArgCombinations(args):
  """Checks for valid combinations of Unity arguments.

  Args:
    args: The parsed command-line arguments.

  Raises:
    arg_parsers.ArgumentTypeError: If an invalid argument combination is found.
  """
  oidc_specified = hasattr(
      args, 'unity_service_principal_application_id'
  ) and args.IsSpecified('unity_service_principal_application_id')

  if not args.IsSpecified('secret_name') and not oidc_specified:
    raise arg_parsers.ArgumentTypeError(
        'Either --secret-name or --unity-service-principal-application-id must'
        ' be specified when federated catalog type is unity.'
    )
  if args.IsSpecified('secret_name') and oidc_specified:
    raise arg_parsers.ArgumentTypeError(
        'Only one of --secret-name or --unity-service-principal-application-id'
        ' can be specified when federated catalog type is unity.'
    )
  if not args.IsSpecified('unity_instance_name'):
    raise arg_parsers.ArgumentTypeError(
        '--unity-instance-name must be specified when federated catalog type'
        ' is unity.'
    )
  if not args.IsSpecified('unity_catalog_name'):
    raise arg_parsers.ArgumentTypeError(
        '--unity-catalog-name must be specified when federated catalog type'
        ' is unity.'
    )
  if args.IsKnownAndSpecified('glue_warehouse'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-warehouse is not supported for Unity federated catalogs.'
    )
  if args.IsKnownAndSpecified('glue_aws_region'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-aws-region is not supported for Unity federated catalogs.'
    )
  if args.IsKnownAndSpecified('glue_aws_role_arn'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-aws-role-arn is not supported for Unity federated catalogs.'
    )
  if args.IsKnownAndSpecified('snowflake_warehouse'):
    raise arg_parsers.ArgumentTypeError(
        '--snowflake-warehouse is not supported for Unity federated catalogs.'
    )
  if args.IsKnownAndSpecified('snowflake_account_identifier'):
    raise arg_parsers.ArgumentTypeError(
        '--snowflake-account-identifier is not supported for Unity federated'
        ' catalogs.'
    )
  if args.IsKnownAndSpecified('workday_base_url'):
    raise arg_parsers.ArgumentTypeError(
        '--workday-base-url is not supported for Unity federated catalogs.'
    )
  if args.IsKnownAndSpecified('workday_tenant'):
    raise arg_parsers.ArgumentTypeError(
        '--workday-tenant is not supported for Unity federated catalogs.'
    )


def CheckValidGlueArgCombinations(args):
  """Checks for valid combinations of Glue arguments.

  Args:
    args: The parsed command-line arguments.

  Raises:
    arg_parsers.ArgumentTypeError: If an invalid argument combination is found.
  """
  if not args.IsSpecified('glue_warehouse'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-warehouse must be specified when federated catalog type is'
        ' glue.'
    )
  if not args.IsSpecified('glue_aws_region'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-aws-region must be specified when federated catalog type is'
        ' glue.'
    )
  if not args.IsSpecified('glue_aws_role_arn'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-aws-role-arn must be specified when federated catalog type is'
        ' glue.'
    )
  if args.IsSpecified('secret_name'):
    raise arg_parsers.ArgumentTypeError(
        '--secret-name is not supported for Glue federated catalogs.'
    )
  if args.IsSpecified('unity_instance_name'):
    raise arg_parsers.ArgumentTypeError(
        '--unity-instance-name is not supported for Glue federated catalogs.'
    )
  if args.IsSpecified('unity_catalog_name'):
    raise arg_parsers.ArgumentTypeError(
        '--unity-catalog-name is not supported for Glue federated catalogs.'
    )
  if args.IsSpecified('unity_service_principal_application_id'):
    raise arg_parsers.ArgumentTypeError(
        '--unity-service-principal-application-id is not supported for Glue'
        ' federated catalogs.'
    )
  if args.IsKnownAndSpecified('snowflake_warehouse'):
    raise arg_parsers.ArgumentTypeError(
        '--snowflake-warehouse is not supported for Glue federated catalogs.'
    )
  if args.IsKnownAndSpecified('snowflake_account_identifier'):
    raise arg_parsers.ArgumentTypeError(
        '--snowflake-account-identifier is not supported for Glue federated'
        ' catalogs.'
    )
  if args.IsKnownAndSpecified('workday_base_url'):
    raise arg_parsers.ArgumentTypeError(
        '--workday-base-url is not supported for Glue federated catalogs.'
    )
  if args.IsKnownAndSpecified('workday_tenant'):
    raise arg_parsers.ArgumentTypeError(
        '--workday-tenant is not supported for Glue federated catalogs.'
    )


def CheckValidSnowflakeArgCombinations(args):
  """Checks for valid combinations of Snowflake arguments.

  Args:
    args: The parsed command-line arguments.

  Raises:
    arg_parsers.ArgumentTypeError: If an invalid argument combination is found.
  """
  if not args.IsSpecified('snowflake_warehouse'):
    raise arg_parsers.ArgumentTypeError(
        '--snowflake-warehouse must be specified when federated catalog type is'
        ' snowflake.'
    )
  if not args.IsSpecified('snowflake_account_identifier'):
    raise arg_parsers.ArgumentTypeError(
        '--snowflake-account-identifier must be specified when federated'
        ' catalog type is snowflake.'
    )
  if not args.IsSpecified('secret_name'):
    raise arg_parsers.ArgumentTypeError(
        '--secret-name must be specified when federated catalog type is'
        ' snowflake.'
    )
  if args.IsSpecified('unity_instance_name'):
    raise arg_parsers.ArgumentTypeError(
        '--unity-instance-name is not supported for Snowflake federated'
        ' catalogs.'
    )
  if args.IsSpecified('unity_catalog_name'):
    raise arg_parsers.ArgumentTypeError(
        '--unity-catalog-name is not supported for Snowflake federated'
        ' catalogs.'
    )
  if args.IsSpecified('unity_service_principal_application_id'):
    raise arg_parsers.ArgumentTypeError(
        '--unity-service-principal-application-id is not supported for'
        ' Snowflake federated catalogs.'
    )
  if args.IsKnownAndSpecified('glue_warehouse'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-warehouse is not supported for Snowflake federated catalogs.'
    )
  if args.IsKnownAndSpecified('glue_aws_region'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-aws-region is not supported for Snowflake federated catalogs.'
    )
  if args.IsKnownAndSpecified('glue_aws_role_arn'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-aws-role-arn is not supported for Snowflake federated catalogs.'
    )
  if args.IsKnownAndSpecified('workday_base_url'):
    raise arg_parsers.ArgumentTypeError(
        '--workday-base-url is not supported for Snowflake federated catalogs.'
    )
  if args.IsKnownAndSpecified('workday_tenant'):
    raise arg_parsers.ArgumentTypeError(
        '--workday-tenant is not supported for Snowflake federated catalogs.'
    )


def CheckValidWorkdayArgCombinations(args):
  """Checks for valid combinations of Workday arguments.

  Args:
    args: The parsed command-line arguments.

  Raises:
    arg_parsers.ArgumentTypeError: If an invalid argument combination is found.
  """
  if not args.IsSpecified('workday_base_url'):
    raise arg_parsers.ArgumentTypeError(
        '--workday-base-url must be specified when federated catalog type is'
        ' workday.'
    )
  if not args.IsSpecified('workday_tenant'):
    raise arg_parsers.ArgumentTypeError(
        '--workday-tenant must be specified when federated catalog type is'
        ' workday.'
    )
  if not args.IsSpecified('secret_name'):
    raise arg_parsers.ArgumentTypeError(
        '--secret-name must be specified when federated catalog type is'
        ' workday.'
    )
  if args.IsSpecified('unity_instance_name'):
    raise arg_parsers.ArgumentTypeError(
        '--unity-instance-name is not supported for Workday federated catalogs.'
    )
  if args.IsSpecified('unity_catalog_name'):
    raise arg_parsers.ArgumentTypeError(
        '--unity-catalog-name is not supported for Workday federated catalogs.'
    )
  if args.IsSpecified('unity_service_principal_application_id'):
    raise arg_parsers.ArgumentTypeError(
        '--unity-service-principal-application-id is not supported for Workday'
        ' federated catalogs.'
    )
  if args.IsKnownAndSpecified('glue_warehouse'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-warehouse is not supported for Workday federated catalogs.'
    )
  if args.IsKnownAndSpecified('glue_aws_region'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-aws-region is not supported for Workday federated catalogs.'
    )
  if args.IsKnownAndSpecified('glue_aws_role_arn'):
    raise arg_parsers.ArgumentTypeError(
        '--glue-aws-role-arn is not supported for Workday federated catalogs.'
    )
  if args.IsKnownAndSpecified('snowflake_warehouse'):
    raise arg_parsers.ArgumentTypeError(
        '--snowflake-warehouse is not supported for Workday federated catalogs.'
    )
  if args.IsKnownAndSpecified('snowflake_account_identifier'):
    raise arg_parsers.ArgumentTypeError(
        '--snowflake-account-identifier is not supported for Workday federated'
        ' catalogs.'
    )


def CheckValidFederatedArgCombinations(args):
  """Checks for valid combinations of federated arguments.

  Ensures that federated-specific flags are only used when `--catalog-type`
  is 'federated', and that required flags are provided for the specific
  federated catalog type.

  Args:
    args: The parsed command-line arguments.

  Raises:
    arg_parsers.ArgumentTypeError: If an invalid argument combination is found.
  """
  federated_flags = [
      'secret_name',
      'unity_catalog_name',
      'unity_instance_name',
      'unity_service_principal_application_id',
      'refresh_interval',
      'namespace_filters',
      'glue_warehouse',
      'glue_aws_region',
      'glue_aws_role_arn',
      'snowflake_warehouse',
      'snowflake_account_identifier',
      'workday_base_url',
      'workday_tenant',
  ]
  is_federated = args.catalog_type == 'federated'
  if is_federated:
    # Check that the federated catalog type is specified for federated catalogs.
    if not args.IsSpecified('federated_catalog_type'):
      raise arg_parsers.ArgumentTypeError(
          '--federated-catalog-type must be specified when catalog type is'
          ' federated.'
      )
    if not args.IsSpecified('primary_location'):
      raise arg_parsers.ArgumentTypeError(
          '--primary-location must be specified when catalog type is federated.'
      )
    if args.federated_catalog_type == 'unity':
      CheckValidUnityArgCombinations(args)
    if args.federated_catalog_type == 'glue':
      CheckValidGlueArgCombinations(args)
    if args.federated_catalog_type == 'snowflake':
      CheckValidSnowflakeArgCombinations(args)
    if args.federated_catalog_type == 'workday':
      CheckValidWorkdayArgCombinations(args)
  else:
    # Check that federated flags are not specified for non-federated catalogs.
    for flag in federated_flags:
      if hasattr(args, flag) and args.IsSpecified(flag):
        raise arg_parsers.ArgumentTypeError(
            '--{} is only supported for federated catalogs.'.format(
                flag.replace('_', '-')
            )
        )


def ProcessNamespaceListResponse(parent_name, response):
  """Processes the response from the list namespaces request."""
  namespaces = []
  if response and 'namespaces' in response:
    for ns_parts in response['namespaces']:
      ns_id = '.'.join(ns_parts)
      namespaces.append(
          types.SimpleNamespace(name=f'{parent_name}/namespaces/{ns_id}')
      )
  page_token = response.get('next-page-token', None)
  unreachable = response.get('unreachable', [])
  return namespaces, page_token, unreachable


def ListNamespaces(parent_name, page_size=None, page_token=None):
  """Lists namespaces in a catalog.

  Args:
      parent_name: name of the catalog in format
        projects/{project}/catalogs/{catalog}.
      page_size: The maximum number of namespaces to return.
      page_token: A page token, received from a previous `ListNamespaces` call.

  Returns:
      A json object that contains namespaces.

  Raises:
      HttpRequestFailError: if error happens with http request, or parsing
          the http response.
  """
  endpoint = apis.GetEffectiveApiEndpoint('biglake', 'v1').strip('/')
  url = (
      f'{endpoint}/iceberg/v1/restcatalog/v1/{parent_name}/namespaces?alt=json'
  )
  if page_size:
    url += f'&pageSize={page_size}'
  if page_token:
    url += f'&pageToken={quote_plus(page_token)}'
  headers = {'Content-Type': 'application/json'}
  response = requests.GetSession().request('GET', url, headers=headers)
  if int(response.status_code) != httplib.OK:
    raise HttpRequestFailError(
        'HTTP request failed. Response: ' + response.text
    )
  try:
    return ProcessNamespaceListResponse(parent_name, json.loads(response.text))
  except ValueError as e:
    raise HttpRequestFailError(
        'No JSON object could be decoded from the HTTP response body: '
        + response.text
    ) from e


def _BuildRefreshOptions(refresh_options_option):
  """Builds the refresh options for the request body."""
  refresh_options = {}
  if (
      hasattr(refresh_options_option, 'refresh_schedule')
      and refresh_options_option.refresh_schedule
  ):
    refresh_schedule = {}
    if (
        hasattr(
            refresh_options_option.refresh_schedule, 'refresh_interval'
        )
        and refresh_options_option.refresh_schedule.refresh_interval
    ):
      refresh_schedule['refresh-interval'] = (
          refresh_options_option.refresh_schedule.refresh_interval
      )
    if refresh_schedule:
      refresh_options['refresh-schedule'] = refresh_schedule
  if (
      hasattr(refresh_options_option, 'refresh_scope')
      and refresh_options_option.refresh_scope
  ):
    refresh_scope = {}
    if (
        hasattr(refresh_options_option.refresh_scope, 'namespace_filters')
        and refresh_options_option.refresh_scope.namespace_filters
    ):
      refresh_scope['namespace-filters'] = (
          refresh_options_option.refresh_scope.namespace_filters
      )
    if refresh_scope:
      refresh_options['refresh-scope'] = refresh_scope
  return refresh_options


def _BuildUnityCatalogInfo(unity_catalog_info_option):
  """Builds the unity catalog info for the request body."""
  unity_catalog_info = {}
  if (
      hasattr(unity_catalog_info_option, 'catalog_name')
      and unity_catalog_info_option.catalog_name
  ):
    unity_catalog_info['catalog-name'] = unity_catalog_info_option.catalog_name
  if (
      hasattr(unity_catalog_info_option, 'instance_name')
      and unity_catalog_info_option.instance_name
  ):
    unity_catalog_info['instance-name'] = (
        unity_catalog_info_option.instance_name
    )
  if (
      hasattr(unity_catalog_info_option, 'service_principal_application_id')
      and unity_catalog_info_option.service_principal_application_id
  ):
    unity_catalog_info['service-principal-application-id'] = (
        unity_catalog_info_option.service_principal_application_id
    )
  return unity_catalog_info


def _BuildGlueCatalogInfo(glue_catalog_info_option: Any) -> Dict[str, Any]:
  """Builds the Glue catalog info for the request body."""
  glue_catalog_info = {
      'warehouse': getattr(glue_catalog_info_option, 'warehouse', None),
      'aws-region': getattr(glue_catalog_info_option, 'aws_region', None),
      'aws-role-arn': getattr(glue_catalog_info_option, 'aws_role_arn', None),
  }
  return {k: v for k, v in glue_catalog_info.items() if v}


def _BuildSnowflakeCatalogInfo(
    snowflake_catalog_info_option: Any,
) -> Dict[str, Any]:
  """Builds the Snowflake catalog info for the request body."""
  snowflake_catalog_info = {
      'warehouse': getattr(snowflake_catalog_info_option, 'warehouse', None),
      'account-identifier': getattr(
          snowflake_catalog_info_option, 'account_identifier', None
      ),
  }
  return {k: v for k, v in snowflake_catalog_info.items() if v}


def _BuildWorkdayCatalogInfo(
    workday_catalog_info_option: Any,
) -> Dict[str, Any]:
  """Builds the Workday catalog info for the request body."""
  workday_catalog_info = {
      'base-url': getattr(workday_catalog_info_option, 'base_url', None),
      'tenant': getattr(workday_catalog_info_option, 'tenant', None),
  }
  return {k: v for k, v in workday_catalog_info.items() if v}


def _BuildFederatedCatalogOptions(options):
  """Builds the federated catalog options for the request body."""
  federated_catalog_options = {}
  if hasattr(options, 'secret_name') and options.secret_name:
    federated_catalog_options['secret-name'] = options.secret_name
  if (
      hasattr(options, 'service_directory_name')
      and options.service_directory_name
  ):
    federated_catalog_options['service-directory-name'] = (
        options.service_directory_name
    )
  if hasattr(options, 'unity_catalog_info') and options.unity_catalog_info:
    unity_catalog_info = _BuildUnityCatalogInfo(options.unity_catalog_info)
    if unity_catalog_info:
      federated_catalog_options['unity-catalog-info'] = unity_catalog_info
  if hasattr(options, 'glue_catalog_info') and options.glue_catalog_info:
    glue_catalog_info = _BuildGlueCatalogInfo(options.glue_catalog_info)
    if glue_catalog_info:
      federated_catalog_options['glue-catalog-info'] = glue_catalog_info
  if (
      hasattr(options, 'snowflake_catalog_info')
      and options.snowflake_catalog_info
  ):
    snowflake_catalog_info = _BuildSnowflakeCatalogInfo(
        options.snowflake_catalog_info
    )
    if snowflake_catalog_info:
      federated_catalog_options['snowflake-catalog-info'] = (
          snowflake_catalog_info
      )
  if hasattr(options, 'workday_catalog_info') and options.workday_catalog_info:
    workday_catalog_info = _BuildWorkdayCatalogInfo(
        options.workday_catalog_info
    )
    if workday_catalog_info:
      federated_catalog_options['workday-catalog-info'] = workday_catalog_info
  if hasattr(options, 'refresh_options') and options.refresh_options:
    refresh_options = _BuildRefreshOptions(options.refresh_options)
    if refresh_options:
      federated_catalog_options['refresh-options'] = refresh_options
  return federated_catalog_options


def CreateCatalog(catalog_id, catalog_msg, primary_location=None):
  """Creates a catalog.

  Args:
      catalog_id: The ID of the catalog.
      catalog_msg: The IcebergCatalog message.
      primary_location: The primary location.

  Returns:
      The created IcebergCatalog message.

  Raises:
      HttpRequestFailError: if error happens with http request, or parsing
          the http response.
  """
  endpoint = apis.GetEffectiveApiEndpoint('biglake', 'v1').strip('/')
  parent_name = GetParentName()
  url = f'{endpoint}/iceberg/v1/restcatalog/extensions/{parent_name}/catalogs?alt=json&iceberg-catalog-id={catalog_id}'
  if primary_location:
    url += f'&primary_location={primary_location}'

  body = {
      'name': catalog_msg.name,
      'catalog-type': str(catalog_msg.catalog_type),
  }
  if catalog_msg.credential_mode:
    body['credential-mode'] = str(catalog_msg.credential_mode)
  if catalog_msg.description:
    body['description'] = catalog_msg.description
  if hasattr(catalog_msg, 'default_location') and catalog_msg.default_location:
    body['default-location'] = catalog_msg.default_location
  if (
      hasattr(catalog_msg, 'restricted_locations_config')
      and catalog_msg.restricted_locations_config
  ):
    body['restricted-locations-config'] = {
        'restricted-locations': (
            catalog_msg.restricted_locations_config.restricted_locations
        )
    }

  if (
      hasattr(catalog_msg, 'federated_catalog_options')
      and catalog_msg.federated_catalog_options
  ):
    body['federated-catalog-options'] = _BuildFederatedCatalogOptions(
        catalog_msg.federated_catalog_options
    )

  headers = {'Content-Type': 'application/json'}
  response = requests.GetSession().request(
      'POST', url, data=json.dumps(body), headers=headers
  )
  if int(response.status_code) != httplib.OK:
    raise HttpRequestFailError(
        'HTTP request failed. Response: ' + response.text
    )
  try:
    response_json = json.loads(response.text)
    return types.SimpleNamespace(
        biglake_service_account=response_json.get('biglake-service-account'),
        biglake_service_account_id=response_json.get(
            'biglake-service-account-id'
        ),
    )
  except ValueError as e:
    raise HttpRequestFailError(
        'No JSON object could be decoded from the HTTP response body: '
        + response.text
    ) from e


def CreateTable(catalog_id, namespace_id, table_data):
  """Creates an Iceberg table.

  Args:
      catalog_id: The ID of the catalog.
      namespace_id: The ID of the namespace.
      table_data: The JSON data for the table creation request.

  Returns:
      The created Iceberg table metadata as JSON.

  Raises:
      HttpRequestFailError: if error happens with http request, or parsing
          the http response.
  """
  endpoint = apis.GetEffectiveApiEndpoint('biglake', 'v1').strip('/')
  parent_name = GetNamespaceName(catalog_id, namespace_id)
  url = f'{endpoint}/iceberg/v1/restcatalog/v1/{parent_name}/tables'
  headers = {'Content-Type': 'application/json'}
  response = requests.GetSession().request(
      'POST', url, data=json.dumps(table_data), headers=headers
  )
  if int(response.status_code) not in [httplib.OK, httplib.CREATED]:
    raise HttpRequestFailError(
        'HTTP request failed. Response: ' + response.text
    )
  return response.text


def GetTable(catalog_id, namespace_id, table_id):
  """Gets Iceberg table metadata.

  Args:
      catalog_id: The ID of the catalog.
      namespace_id: The ID of the namespace.
      table_id: The ID of the table.

  Returns:
      The Iceberg table metadata as JSON.

  Raises:
      HttpRequestFailError: if error happens with HTTP request, or parsing
          the http response.
  """
  endpoint = apis.GetEffectiveApiEndpoint('biglake', 'v1').strip('/')
  table_name = GetTableName(catalog_id, namespace_id, table_id)
  url = f'{endpoint}/iceberg/v1/restcatalog/v1/{table_name}?alt=json&snapshots=refs'
  headers = {'Content-Type': 'application/json'}
  response = requests.GetSession().request('GET', url, headers=headers)
  if int(response.status_code) != httplib.OK:
    raise HttpRequestFailError(
        'HTTP request failed. Response: ' + response.text
    )
  return response.text


def UpdateTable(catalog_id, namespace_id, table_id, table_data):
  """Updates an Iceberg table.

  Args:
      catalog_id: The ID of the catalog.
      namespace_id: The ID of the namespace.
      table_id: The ID of the table.
      table_data: The JSON data for the table update request.

  Returns:
      The updated Iceberg table metadata as JSON.

  Raises:
      HttpRequestFailError: if error happens with http request, or parsing
          the http response.
  """
  endpoint = apis.GetEffectiveApiEndpoint('biglake', 'v1').strip('/')
  table_name = GetTableName(catalog_id, namespace_id, table_id)
  url = f'{endpoint}/iceberg/v1/restcatalog/v1/{table_name}?alt=json'
  headers = {'Content-Type': 'application/json'}
  response = requests.GetSession().request(
      'POST', url, data=json.dumps(table_data), headers=headers
  )
  if int(response.status_code) not in [httplib.OK, httplib.CREATED]:
    raise HttpRequestFailError(
        'HTTP request failed. Response: ' + response.text
    )
  return response.text
