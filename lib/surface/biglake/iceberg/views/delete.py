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
"""The delete command for BigLake Iceberg REST catalogs views."""

import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

help_text = textwrap.dedent("""\
    To delete a view in parent catalog `my-catalog` and namespace `my-namespace`, run:

      $ {command} my-view --namespace=my-namespace --catalog=my-catalog
    """)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
class Delete(base.DeleteCommand):
  """Delete a BigLake Iceberg view."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddViewResourceArg(parser, 'to delete', positional=True)

  def Run(self, args):
    view_ref = args.CONCEPTS.view.Parse()
    view_name = util.GetViewName(
        view_ref.catalogsId,
        view_ref.namespacesId,
        view_ref.viewsId,
        project_id=view_ref.projectsId,
    )

    console_io.PromptContinue(
        message='Delete view [{}]?'.format(view_name),
        cancel_on_no=True,
    )

    util.DeleteView(
        view_ref.catalogsId,
        view_ref.namespacesId,
        view_ref.viewsId,
        project_id=view_ref.projectsId,
    )

    log.DeletedResource(view_name, 'view')
