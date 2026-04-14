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
"""The create command for BigLake Iceberg REST catalogs namespaces."""

import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import log


help_text = textwrap.dedent("""\
    To create a namespace in parent catalog `my-catalog`, run:

      $ {command} my-namespace --catalog=my-catalog

    To create a namespace in parent catalog `my-catalog`, with properties `key1=value1,key2=value2`, run:

      $ {command} my-namespace --catalog=my-catalog --properties=key1=value1,key2=value2
    """)


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.DefaultUniverseOnly
class CreateNamespace(base.CreateCommand):
  """Create a BigLake Iceberg REST namespace."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddNamespaceResourceArg(parser, 'to create', positional=True)
    arguments.AddPropertiesArg(parser)

  def Run(self, args):
    client = util.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE

    processed_namespaces = args.namespace.split(',')

    properties = None
    if args.properties:
      properties = messages.IcebergNamespace.PropertiesValue(
          additionalProperties=[
              messages.IcebergNamespace.PropertiesValue.AdditionalProperty(
                  key=k, value=v
              )
              for k, v in args.properties.items()
          ]
      )

    namespace = messages.IcebergNamespace(
        namespace=processed_namespaces,
        properties=properties,
    )

    request = messages.BiglakeIcebergV1RestcatalogV1ProjectsCatalogsNamespacesCreateRequest(
        icebergNamespace=namespace,
        parent=util.GetCatalogName(args.catalog),
    )

    response = (
        client.iceberg_v1_restcatalog_v1_projects_catalogs_namespaces.Create(
            request
        )
    )

    for ns in response.namespace:
      log.CreatedResource(
          util.GetNamespaceName(args.catalog, ns),
          'namespace',
      )
    return response
