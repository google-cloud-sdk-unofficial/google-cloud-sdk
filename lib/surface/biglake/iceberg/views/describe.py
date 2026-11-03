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
"""The describe command for BigLake Iceberg REST catalogs views."""

import json
import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import flags


help_text = textwrap.dedent("""\
    To describe view `my-view` in parent catalog `my-catalog` and namespace `my-namespace`, run:

      $ {command} my-view --namespace=my-namespace --catalog=my-catalog
    """)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
class Describe(base.DescribeCommand):
  """Describe a BigLake Iceberg view."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddViewResourceArg(parser, 'to describe', positional=True)

  def Run(self, args):
    view_ref = args.CONCEPTS.view.Parse()
    response_json = util.GetView(
        view_ref.catalogsId,
        view_ref.namespacesId,
        view_ref.viewsId,
        project_id=view_ref.projectsId,
    )
    return json.loads(response_json)
