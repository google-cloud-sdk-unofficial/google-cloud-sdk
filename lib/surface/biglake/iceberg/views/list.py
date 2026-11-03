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
"""The list command for BigLake Iceberg REST views."""

import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import flags


help_text = textwrap.dedent("""\
    To list views in parent catalog `my-catalog` and namespace `my-namespace`, run:

      $ {command} --namespace=my-namespace --catalog=my-catalog
    """)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
class ListIcebergViews(base.ListCommand):
  """List BigLake Iceberg REST views."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @staticmethod
  def Args(parser):
    flags.AddNamespaceResourceArg(
        parser, 'to list views from', positional=False
    )
    parser.display_info.AddFormat("""
          table(
            name:sort=1,
            namespace:label=NAMESPACE
          )
        """)

  def Run(self, args):
    namespace_ref = args.CONCEPTS.namespace.Parse()
    catalog_id = namespace_ref.catalogsId
    namespace_id = namespace_ref.namespacesId
    project_id = namespace_ref.projectsId
    page_token = None
    while True:
      response = util.ListViews(
          catalog_id,
          namespace_id,
          page_size=args.page_size,
          page_token=page_token,
          project_id=project_id,
      )
      identifiers = response.get('identifiers', [])
      for identifier in identifiers:
        yield identifier
      page_token = response.get('next-page-token') or response.get(
          'nextPageToken'
      )
      if not page_token:
        break
