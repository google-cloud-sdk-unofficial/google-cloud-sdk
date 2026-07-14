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
"""The publish command for Data Product Sharing."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA
)
@base.DefaultUniverseOnly
class PublishDataProduct(base.Command):
  """Publish a Knowledge Catalog Data Product or BigLake tables to external partners."""

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
    source_group = parser.add_group('source', mutex=True, required=True)
    delta_sharing_catalog_resource = presentation_specs.ResourcePresentationSpec(
        '--connection-catalog',
        GetCatalogResourceSpec(),
        'The delta sharing catalog that contains information about where the '
        'data product is published.',
        prefixes=True,
        required=True)
    irc_catalog_resource = presentation_specs.ResourcePresentationSpec(
        '--iceberg-catalog',
        GetCatalogResourceSpec(),
        'The BigLake Iceberg REST Catalog whose tables will be published.',
        prefixes=True,
        group=source_group)
    concept_parsers.ConceptParser(
        [delta_sharing_catalog_resource, irc_catalog_resource]
    ).AddToParser(parser)
    source_group.add_argument(
        '--data-product',
        help='The Knowledge Catalog Data Product to publish.',
    )
    parser.add_argument(
        '--share',
        help='The desired name of the Share as it will be published to',
        required=True,
    )
    parser.add_argument(
        '--sap-federated-identity-provider',
        help=('The resource name of the Workload Identity Federation (WIF) '
              'provider resource representing the SAP federated identity. You '
              'must manually grant this identity the necessary IAM permissions '
              '(e.g., roles/biglake.viewer) on the underlying catalog.'),
        required=True,
    )
    parser.add_argument(
        '--title',
        help=(
            'The title of the published share. Required when publishing an'
            ' Iceberg catalog.'
        ),
    )
    parser.add_argument(
        '--short-description',
        help=(
            'The short, concise description of the published share. Required'
            ' when publishing an Iceberg catalog.'
        ),
    )
    parser.add_argument(
        '--description',
        help='The optional detailed description of the published share.',
    )

  def Run(self, args):
    client = apis.GetClientInstance('biglake', 'data_product_sharing_v1alpha')
    messages = client.MESSAGES_MODULE
    iceberg_catalog_ref = None
    if args.iceberg_catalog:
      iceberg_catalog_ref = messages.IcebergCatalogReference(
          catalog=args.CONCEPTS.iceberg_catalog.Parse().RelativeName(),
          title=args.title,
          shortDescription=args.short_description,
          description=args.description,
      )
    data_product_ref = None
    if args.data_product:
      data_product_ref = messages.DataProductReference(
          dataProduct=args.data_product
      )
    return client.dataproductsharing_v1alpha_projects_catalogs.PublishDataProduct(
        messages.BiglakeDataproductsharingV1alphaProjectsCatalogsPublishDataProductRequest(
            connectionCatalog=args.CONCEPTS.connection_catalog.Parse().RelativeName(),
            publishDataProductRequest=messages.PublishDataProductRequest(
                share=args.share,
                dataProduct=data_product_ref,
                icebergCatalog=iceberg_catalog_ref,
                sapFederatedIdentityProvider=args.sap_federated_identity_provider,
            ),
        )
    )
