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
"""The register command for BigLake Iceberg REST catalogs tables."""

import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import log


help_text = textwrap.dedent("""\
    To register table `my-table` in parent catalog `my-catalog` and namespace `my-namespace`, run:

      $ {command} my-table --namespace=my-namespace --catalog=my-catalog --metadata-location=gs://my-bucket/metadata.json

    To overwrite table `my-table` in parent catalog `my-catalog` and namespace `my-namespace`, run:

      $ {command} my-table --namespace=my-namespace --catalog=my-catalog --metadata-location=gs://my-bucket/metadata.json --overwrite
    """)


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.DefaultUniverseOnly
class Register(base.CreateCommand):
  """Register a BigLake Iceberg table."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddTableResourceArg(parser, 'to register', positional=True)
    arguments.AddTableRegisterArgs(parser)

  def Run(self, args):
    client = util.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE

    table_ref = args.CONCEPTS.table.Parse()

    register_request = messages.RegisterIcebergTableRequest(
        name=table_ref.tablesId,
        metadata_location=args.metadata_location,
        overwrite=args.overwrite,
    )

    request = messages.BiglakeIcebergV1RestcatalogV1ProjectsCatalogsNamespacesRegisterRequest(
        parent=util.GetNamespaceName(
            table_ref.catalogsId, table_ref.namespacesId
        ),
        registerIcebergTableRequest=register_request,
    )

    response = (
        client.iceberg_v1_restcatalog_v1_projects_catalogs_namespaces.Register(
            request
        )
    )

    log.CreatedResource(
        util.GetTableName(
            table_ref.catalogsId, table_ref.namespacesId, table_ref.tablesId
        ),
        'table',
    )
    return response
