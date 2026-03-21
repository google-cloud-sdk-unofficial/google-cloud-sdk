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
"""The list command for BigLake Iceberg REST tables."""
import textwrap

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import flags


help_text = textwrap.dedent("""\
    To list tables in parent catalog `my-catalog` and namespace `my-namespace`, run:

      $ {command} --namespace=my-namespace --catalog=my-catalog
    """)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class ListIcebergTables(base.ListCommand):
  """List BigLake Iceberg REST tables."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @staticmethod
  def Args(parser):
    flags.AddNamespaceResourceArg(
        parser, 'to list tables from', positional=False
    )
    parser.display_info.AddFormat("""
          table(
            name:sort=1,
            namespace:label=NAMESPACE
          )
        """)

  def Run(self, args):
    client = util.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE

    namespace_name = util.GetNamespaceName(args.catalog, args.namespace)
    request = messages.BiglakeIcebergV1RestcatalogV1ProjectsCatalogsNamespacesTablesListRequest(
        parent=namespace_name
    )

    return list_pager.YieldFromList(
        client.iceberg_v1_restcatalog_v1_projects_catalogs_namespaces_tables,
        request,
        next_token_attribute='next_page_token',
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='identifiers',
    )
