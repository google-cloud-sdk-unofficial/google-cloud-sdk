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
"""The list command for BigLake Iceberg REST namespaces."""

import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import log


help_text = textwrap.dedent("""\
    To list namespaces in parent catalog `my-catalog`, run:
      $ {command} --catalog=my-catalog
""")


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class ListIcebergNamespaces(base.ListCommand):
  """List BigLake Iceberg REST namespaces."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @staticmethod
  def Args(parser):
    flags.AddCatalogResourceArg(parser, 'to list', positional=False)
    parser.display_info.AddFormat("""
          table(
            name:sort=1,
            name.basename():label=NAMESPACE-ID
          )
        """)

  def Run(self, args):
    parent_name = util.GetCatalogName(args.catalog)
    page_token = None
    unreachable = set()
    while True:
      namespaces, page_token, unreachable_in_page = util.ListNamespaces(
          parent_name, page_size=args.page_size, page_token=page_token
      )
      unreachable.update(unreachable_in_page)
      for ns in namespaces:
        yield ns
      if not page_token:
        break
    if unreachable:
      log.warning(
          'The following namespaces were unreachable: {}.'
          .format(', '.join(sorted(unreachable))))
