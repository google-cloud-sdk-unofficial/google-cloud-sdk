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
"""The unpublish command for Data Product Sharing."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class UnpublishDataProduct(base.Command):
  """Unpublish a Knowledge Catalog Data Product or BigLake tables from external partners."""

  @staticmethod
  def Args(parser):
    def GetCatalogResourceSpec():
      return concepts.ResourceSpec(
          'biglake.dataproductsharing.v1alpha.projects.catalogs',
          resource_name='catalog',
          projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
          catalogsId=concepts.ResourceParameterAttributeConfig('catalog'),
          api_version='data_product_sharing_v1alpha',
      )

    source_group = parser.add_group('source', mutex=True)
    delta_sharing_catalog_resource = presentation_specs.ResourcePresentationSpec(
        '--connection-catalog',
        GetCatalogResourceSpec(),
        'The delta sharing catalog that contains information about where the '
        'data product is published.',
        prefixes=True,
        required=True,
    )
    irc_catalog_resource = presentation_specs.ResourcePresentationSpec(
        '--iceberg-catalog',
        GetCatalogResourceSpec(),
        'The BigLake Iceberg REST Catalog whose tables will be unpublished and '
        'have permissions revoked.',
        prefixes=True,
        group=source_group,
    )
    concept_parsers.ConceptParser(
        [delta_sharing_catalog_resource, irc_catalog_resource]
    ).AddToParser(parser)
    source_group.add_argument(
        '--data-product',
        help='The Knowledge Catalog Data Product to unpublish.',
    )
    parser.add_argument(
        '--share',
        help='The name of the Share to unpublish from external partners.',
        required=True,
    )
    parser.add_argument(
        '--sap-federated-identity-provider',
        help=(
            'The resource name of the Workload Identity Federation (WIF) '
            'provider resource representing the SAP federated identity. If '
            'provided along with --iceberg-catalog or --data-product, '
            'table-level WIF IAM permissions (e.g., roles/biglake.viewer) '
            'granted during publish will be automatically revoked.'
        ),
    )

  def Run(self, args):
    if (
        args.iceberg_catalog or args.data_product
    ) and not args.sap_federated_identity_provider:
      raise exceptions.RequiredArgumentException(
          '--sap-federated-identity-provider',
          'Must be specified when --iceberg-catalog or --data-product is'
          ' specified.',
      )

    client = apis.GetClientInstance('biglake', 'data_product_sharing_v1alpha')
    messages = client.MESSAGES_MODULE
    iceberg_catalog_ref = None
    if args.iceberg_catalog:
      iceberg_catalog_ref = messages.IcebergCatalogReference(
          catalog=args.CONCEPTS.iceberg_catalog.Parse().RelativeName()
      )
    data_product_ref = None
    if args.data_product:
      data_product_ref = messages.DataProductReference(
          dataProduct=args.data_product
      )
    response = client.dataproductsharing_v1alpha_projects_catalogs.UnpublishDataProduct(
        messages.BiglakeDataproductsharingV1alphaProjectsCatalogsUnpublishDataProductRequest(
            connectionCatalog=args.CONCEPTS.connection_catalog.Parse().RelativeName(),
            unpublishDataProductRequest=messages.UnpublishDataProductRequest(
                share=args.share,
                dataProduct=data_product_ref,
                icebergCatalog=iceberg_catalog_ref,
                sapFederatedIdentityProvider=args.sap_federated_identity_provider,
            ),
        )
    )
    log.status.Print('Successfully unpublished share [{0}].'.format(args.share))
    return response
