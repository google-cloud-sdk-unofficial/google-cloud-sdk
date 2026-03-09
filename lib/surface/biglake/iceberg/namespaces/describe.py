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
"""The describe command for BigLake Iceberg REST catalogs namespaces."""

import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import flags

help_text = textwrap.dedent("""\
    To describe a namespace in parent catalog `my-catalog`, run:

      $ {command} my-namespace --catalog=my-catalog
    """)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class DescribeCatalog(base.DescribeCommand):
  """Describe a BigLake Iceberg REST namespace."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @staticmethod
  def Args(parser):
    flags.AddNamespaceResourceArg(parser, 'to describe')

  def Run(self, args):
    client = util.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE

    namespace_name = util.GetNamespaceName(args.catalog, args.namespace)

    request = messages.BiglakeIcebergV1RestcatalogV1ProjectsCatalogsNamespacesGetRequest(
        name=namespace_name
    )

    return client.iceberg_v1_restcatalog_v1_projects_catalogs_namespaces.Get(
        request
    )
