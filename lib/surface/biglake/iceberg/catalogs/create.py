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
"""The create command for BigLake Iceberg REST catalogs."""

import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.util import times

help_text = textwrap.dedent("""\
    To add a catalog using a Cloud Storage bucket `my-catalog-bucket`, run:

      $ {command} my-catalog-bucket --catalog-type=gcs-bucket

    To create a catalog using a Cloud Storage bucket `my-catalog-bucket` with vended credentials, run:

      $ {command} my-catalog-bucket --catalog-type=gcs-bucket --credential-mode=vended-credentials
    """)


def _BuildFederatedCatalogMessage(args, messages):
  """Builds FederatedCatalogMessage for federated catalogs."""
  if args.federated_catalog_type == 'unity':
    federated_catalog_options = messages.FederatedCatalogOptions(
        service_directory_name=args.service_directory_name,
        secret_name=args.secret_name,
        unity_catalog_info=messages.UnityCatalogInfo(
            instance_name=args.unity_instance_name,
            catalog_name=args.unity_catalog_name,
        ),
    )
  else:
    federated_catalog_options = messages.FederatedCatalogOptions()
  # Refresh options are supported for all federated catalog types.
  refresh_options = messages.RefreshOptions()
  if args.refresh_interval:
    refresh_options.refresh_schedule = messages.RefreshSchedule(
        refresh_interval=times.FormatDurationForJson(
            times.ParseDuration(str(args.refresh_interval) + 's')
        )
    )
  if args.namespace_filters:
    refresh_options.refresh_scope = messages.RefreshScope(
        namespace_filters=args.namespace_filters
    )
  federated_catalog_options.refresh_options = refresh_options
  return federated_catalog_options


@base.ReleaseTracks(
    base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.DefaultUniverseOnly
class CreateCatalog(base.CreateCommand):
  """Create a BigLake Iceberg REST catalog."""

  detailed_help = {
      'EXAMPLES': help_text,
  }
  # Not supported in beta yet.
  _support_catalog_type_biglake = False
  _support_primary_location = False
  _support_service_directory_name = False
  _support_federated_catalog = False

  @classmethod
  def Args(cls, parser):
    flags.AddCatalogResourceArg(parser, 'to create')
    arguments.AddDescriptionArg(parser)
    util.GetCredentialModeEnumMapper(
        cls.ReleaseTrack()
    ).choice_arg.AddToParser(parser)
    util.GetCatalogTypeEnumMapper(
        cls.ReleaseTrack()
    ).choice_arg.AddToParser(parser)
    if cls._support_primary_location:
      arguments.AddCatalogsCreateArgs(parser)
    if cls._support_federated_catalog:
      arguments.AddFederatedCatalogArgs(parser)
    if cls._support_catalog_type_biglake:
      util.AddDefaultLocationArg(parser)
      util.AddAdditionalLocationsArg(parser)
    if cls._support_service_directory_name:
      arguments.AddServiceDirectoryNameArg(parser)

  def Run(self, args):
    if self._support_catalog_type_biglake:
      util.CheckValidArgCombinations(args)
    if self._support_federated_catalog:
      util.CheckValidFederatedArgCombinations(args)
    client = util.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE

    catalog_name = util.GetCatalogName(args.catalog)

    credential_mode = None
    if args.IsSpecified('credential_mode'):
      credential_mode = util.GetCredentialModeEnumMapper(
          self.ReleaseTrack()
      ).GetEnumForChoice(args.credential_mode)

    catalog = messages.IcebergCatalog(
        name=catalog_name,
        catalog_type=util.GetCatalogTypeEnumMapper(
            self.ReleaseTrack()
        ).GetEnumForChoice(args.catalog_type),
        credential_mode=credential_mode,
    )
    if args.IsSpecified('description'):
      catalog.description = args.description
    if self._support_catalog_type_biglake:
      catalog.default_location = args.default_location
      catalog.additional_locations = args.additional_locations or []

    if self._support_federated_catalog and args.catalog_type == 'federated':
      catalog.federated_catalog_options = _BuildFederatedCatalogMessage(
          args, messages
      )

    response = util.CreateCatalog(
        args.catalog,
        catalog,
        primary_location=(
            args.primary_location if self._support_primary_location else None
        ),
    )
    if response:
      log.CreatedResource(catalog_name, 'catalog')
      if response.biglake_service_account:
        log.status.Print(
            'BigLake service account: {}'.format(
                response.biglake_service_account
            )
        )
      if response.biglake_service_account_id:
        log.status.Print(
            'BigLake service account ID: {}'.format(
                response.biglake_service_account_id
            )
        )
    return response


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateCatalog):
  """Create a BigLake Iceberg REST catalog."""
  detailed_help = {
      'EXAMPLES': help_text,
  }
  _support_catalog_type_biglake = True
  _support_primary_location = True
  _support_service_directory_name = True
  _support_federated_catalog = True
