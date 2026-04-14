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

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.util import times


@base.ReleaseTracks(
    base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.DefaultUniverseOnly
class UpdateCatalog(base.UpdateCommand):
  """Update a BigLake Iceberg REST catalog."""

  # Not supported in beta yet.
  _support_catalog_type_biglake = False
  _support_service_directory_name = False
  _support_federated_catalog = False

  @classmethod
  def Args(cls, parser):
    flags.AddCatalogResourceArg(parser, 'to update')
    util.GetCredentialModeEnumMapper(
        cls.ReleaseTrack()
    ).choice_arg.AddToParser(parser)
    if cls._support_catalog_type_biglake:
      util.GetUpdateCatalogTypeEnumMapper(
          base.ReleaseTrack.ALPHA
      ).choice_arg.AddToParser(parser)
      util.AddAdditionalLocationsArg(parser)
    if cls._support_service_directory_name:
      arguments.AddServiceDirectoryNameArg(parser)
    if cls._support_federated_catalog:
      arguments.AddUpdateFederatedCatalogArgs(parser)

  def _UpdateFederatedCatalogOptions(
      self, args, catalog, messages, update_mask
  ):
    """Updates catalog with federated catalog options."""
    catalog.federated_catalog_options = messages.FederatedCatalogOptions()
    if self._support_service_directory_name and args.IsSpecified(
        'service_directory_name'
    ):
      update_mask.append('federated_catalog_options.service_directory_name')
      catalog.federated_catalog_options.service_directory_name = (
          args.service_directory_name
      )
    if args.IsSpecified('secret_name'):
      update_mask.append('federated_catalog_options.secret_name')
      catalog.federated_catalog_options.secret_name = args.secret_name
    if args.IsSpecified('refresh_interval') or args.IsSpecified(
        'namespace_filters'
    ):
      catalog.federated_catalog_options.refresh_options = (
          messages.RefreshOptions()
      )
    if args.IsSpecified('refresh_interval'):
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
    if args.IsSpecified('namespace_filters'):
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

    get_request = messages.BiglakeIcebergV1RestcatalogExtensionsProjectsCatalogsGetRequest(
        name=catalog_name
    )

    get_response = (
        client.iceberg_v1_restcatalog_extensions_projects_catalogs.Get(
            get_request
        )
    )
    catalog_type = get_response.catalog_type
    if (
        self._support_catalog_type_biglake
        and args.IsSpecified('catalog_type')
        and args.catalog_type == 'biglake'
    ):
      update_mask.append('catalog_type')
      catalog_type = util.GetUpdateCatalogTypeEnumMapper(
          self.ReleaseTrack()
      ).GetEnumForChoice(args.catalog_type)
    additional_locations = []
    if self._support_catalog_type_biglake and args.IsSpecified(
        'additional_locations'
    ):
      update_mask.append('additional_locations')
      additional_locations = args.additional_locations

    catalog = messages.IcebergCatalog(
        name=catalog_name,
        catalog_type=catalog_type,
        credential_mode=credential_mode,
    )

    if self._support_federated_catalog:
      if (
          args.IsSpecified('service_directory_name')
          or args.IsSpecified('secret_name')
          or args.IsSpecified('refresh_interval')
          or args.IsSpecified('namespace_filters')
      ):
        self._UpdateFederatedCatalogOptions(
            args, catalog, messages, update_mask
        )

    if self._support_catalog_type_biglake:
      catalog.additional_locations = additional_locations
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


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateCatalog):
  """Update a BigLake Iceberg REST catalog."""
  _support_catalog_type_biglake = True
  _support_service_directory_name = True
  _support_federated_catalog = True
