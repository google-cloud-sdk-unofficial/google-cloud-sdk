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
"""The update command for BigLake Iceberg REST catalogs."""

import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.util import times


help_text = textwrap.dedent("""\
    To update the description of a catalog `my-catalog`, run:

      $ {command} my-catalog --description="updated description"
    """)

help_text_alpha = textwrap.dedent("""\
    To update the refresh interval and namespace filters for a federated catalog `my-federated-catalog`, run:

      $ {command} my-federated-catalog --refresh-interval=1h --namespace-filters=db1,db2
    """)


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class UpdateCatalog(base.UpdateCommand):
  """Update a BigLake Iceberg REST catalog."""

  detailed_help = {
      'EXAMPLES': help_text,
  }
  # Not supported in GA yet.
  _support_service_directory_name = False
  _support_federated_catalog = False
  _support_unity_service_principal_application_id = False
  _support_glue_catalog = False

  @classmethod
  def Args(cls, parser):
    flags.AddCatalogResourceArg(parser, 'to update')
    arguments.AddDescriptionArg(parser)
    util.GetCredentialModeEnumMapper(
        cls.ReleaseTrack()
    ).choice_arg.AddToParser(parser)
    util.GetUpdateCatalogTypeEnumMapper(
        cls.ReleaseTrack()
    ).choice_arg.AddToParser(parser)
    arguments.AddRestrictedLocationsArg(parser)
    if cls._support_service_directory_name:
      arguments.AddServiceDirectoryNameArg(parser)
    if cls._support_unity_service_principal_application_id:
      arguments.AddUnityServicePrincipalApplicationIdArg(parser)
    if cls._support_glue_catalog:
      arguments.AddGlueAwsRoleArnArg(parser)
    if cls._support_federated_catalog:
      arguments.AddUpdateFederatedCatalogArgs(parser)

  def _UpdateFederatedCatalogOptions(
      self, args, catalog, messages, update_mask
  ):
    """Updates catalog with federated catalog options."""
    catalog.federated_catalog_options = messages.FederatedCatalogOptions()
    if args.IsKnownAndSpecified('service_directory_name'):
      update_mask.append('federated_catalog_options.service_directory_name')
      catalog.federated_catalog_options.service_directory_name = (
          args.service_directory_name
      )
    if args.IsKnownAndSpecified('secret_name'):
      update_mask.append('federated_catalog_options.secret_name')
      catalog.federated_catalog_options.secret_name = args.secret_name
    if args.IsKnownAndSpecified('unity_service_principal_application_id'):
      update_mask.append(
          'federated_catalog_options.unity_catalog_info.service_principal_application_id'
      )
      catalog.federated_catalog_options.unity_catalog_info = messages.UnityCatalogInfo(
          service_principal_application_id=args.unity_service_principal_application_id
      )
    if args.IsKnownAndSpecified('glue_aws_role_arn'):
      update_mask.append(
          'federated_catalog_options.glue_catalog_info.aws_role_arn'
      )
      catalog.federated_catalog_options.glue_catalog_info = (
          messages.GlueCatalogInfo(aws_role_arn=args.glue_aws_role_arn)
      )
    if args.IsKnownAndSpecified('refresh_interval') or args.IsKnownAndSpecified(
        'namespace_filters'
    ):
      catalog.federated_catalog_options.refresh_options = (
          messages.RefreshOptions()
      )
    if args.IsKnownAndSpecified('refresh_interval'):
      update_mask.append(
          'federated_catalog_options.refresh_options.refresh_schedule'
      )
      catalog.federated_catalog_options.refresh_options.refresh_schedule = (
          messages.RefreshSchedule(
              refresh_interval=times.FormatDurationForJson(
                  times.ParseDuration(str(args.refresh_interval) + 's')
              )
          )
      )
    if args.IsKnownAndSpecified('namespace_filters'):
      update_mask.append(
          'federated_catalog_options.refresh_options.refresh_scope'
      )
      catalog.federated_catalog_options.refresh_options.refresh_scope = (
          messages.RefreshScope(namespace_filters=args.namespace_filters)
      )

  def Run(self, args):
    client = util.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE

    catalog_name = util.GetCatalogName(args.catalog)

    update_mask = []
    credential_mode = None
    if args.IsSpecified('credential_mode'):
      update_mask.append('credential_mode')
      credential_mode = util.GetCredentialModeEnumMapper(
          self.ReleaseTrack()
      ).GetEnumForChoice(args.credential_mode)
    description = None
    if args.IsSpecified('description'):
      update_mask.append('description')
      description = args.description

    get_request = messages.BiglakeIcebergV1RestcatalogExtensionsProjectsCatalogsGetRequest(
        name=catalog_name
    )

    get_response = (
        client.iceberg_v1_restcatalog_extensions_projects_catalogs.Get(
            get_request
        )
    )
    catalog_type = get_response.catalog_type

    is_federated = (
        catalog_type
        == messages.IcebergCatalog.CatalogTypeValueValuesEnum.CATALOG_TYPE_FEDERATED
    )

    if (
        args.IsKnownAndSpecified('secret_name')
        or args.IsKnownAndSpecified('unity_service_principal_application_id')
        or args.IsKnownAndSpecified('glue_aws_role_arn')
        or args.IsKnownAndSpecified('refresh_interval')
        or args.IsKnownAndSpecified('namespace_filters')
        or args.IsKnownAndSpecified('service_directory_name')
    ):
      if not is_federated:
        raise exceptions.InvalidArgumentException(
            '--',
            'Cannot specify federated catalog arguments for a non-federated'
            ' catalog.',
        )

      is_glue = (
          get_response.federated_catalog_options
          and get_response.federated_catalog_options.glue_catalog_info
      )
      is_unity = (
          get_response.federated_catalog_options
          and get_response.federated_catalog_options.unity_catalog_info
      )

      if is_glue and args.IsKnownAndSpecified(
          'unity_service_principal_application_id'
      ):
        raise exceptions.InvalidArgumentException(
            '--unity-service-principal-application-id',
            '--unity-service-principal-application-id is not supported for Glue'
            ' federated catalogs.',
        )

      if is_glue and args.IsKnownAndSpecified('secret_name'):
        raise exceptions.InvalidArgumentException(
            '--secret-name',
            '--secret-name is not supported for Glue federated catalogs.',
        )

      if is_unity and args.IsKnownAndSpecified('glue_aws_role_arn'):
        raise exceptions.InvalidArgumentException(
            '--glue-aws-role-arn',
            'Cannot specify Glue Catalog arguments when updating a Unity'
            ' federated catalog.',
        )
    if (
        args.IsSpecified('catalog_type')
        and args.catalog_type == 'biglake'
    ):
      update_mask.append('catalog_type')
      catalog_type = util.GetUpdateCatalogTypeEnumMapper(
          self.ReleaseTrack()
      ).GetEnumForChoice(args.catalog_type)
    restricted_locations = []
    if args.IsSpecified(
        'restricted_locations'
    ):
      update_mask.append('restricted_locations_config.restricted_locations')
      restricted_locations = args.restricted_locations

    catalog = messages.IcebergCatalog(
        name=catalog_name,
        catalog_type=catalog_type,
        credential_mode=credential_mode,
        description=description,
    )

    if self._support_federated_catalog:
      if (
          args.IsKnownAndSpecified('service_directory_name')
          or args.IsKnownAndSpecified('secret_name')
          or args.IsKnownAndSpecified('unity_service_principal_application_id')
          or args.IsKnownAndSpecified('glue_aws_role_arn')
          or args.IsKnownAndSpecified('refresh_interval')
          or args.IsKnownAndSpecified('namespace_filters')
      ):
        self._UpdateFederatedCatalogOptions(
            args, catalog, messages, update_mask
        )

    if args.IsSpecified(
        'restricted_locations'
    ):
      catalog.restricted_locations_config = messages.RestrictedLocationsConfig(
          restricted_locations=restricted_locations
      )
    request = messages.BiglakeIcebergV1RestcatalogExtensionsProjectsCatalogsPatchRequest(
        name=catalog_name,
        icebergCatalog=catalog,
        updateMask=','.join(update_mask),
    )
    response = client.iceberg_v1_restcatalog_extensions_projects_catalogs.Patch(
        request
    )
    if response:
      log.UpdatedResource(catalog_name, 'catalog')
      if response.biglake_service_account:
        log.status.Print(
            'BigLake service account: {}'.format(
                response.biglake_service_account
            )
        )
      if response.biglake_service_account_id:
        log.status.Print(
            'BigLake service account unique ID: {}'.format(
                response.biglake_service_account_id
            )
        )
    return response


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(UpdateCatalog):
  """Update a BigLake Iceberg REST catalog."""
  detailed_help = {
      'EXAMPLES': help_text + '\n\n' + help_text_alpha,
  }
  _support_federated_catalog = True
  _support_unity_service_principal_application_id = True
  _support_glue_catalog = True


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update a BigLake Iceberg REST catalog."""

  _support_service_directory_name = True
  _support_unity_service_principal_application_id = True
  _support_glue_catalog = True
