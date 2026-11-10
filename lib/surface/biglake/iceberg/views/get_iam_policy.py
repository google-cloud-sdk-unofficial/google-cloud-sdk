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
"""Command to get the IAM policy for a BigLake Iceberg REST catalog view."""

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.command_lib.iam import iam_util


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for a BigLake Iceberg REST catalog view."""

  detailed_help = {
      'DESCRIPTION': (
          'Gets the IAM policy for a BigLake Iceberg REST catalog view.'
      ),
      'EXAMPLES': (
          """\
          To get the IAM policy for the catalog `my-catalog`, namespace `my-namespace`, and view `my-view` run:

            $ {command} my-view --catalog=my-catalog --namespace=my-namespace
          """
      ),
  }

  @staticmethod
  def Args(parser):
    flags.AddViewResourceArg(parser, 'to get the IAM policy for')
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = util.GetClientInstance(self.ReleaseTrack())
    messages = util.GetMessagesModule(self.ReleaseTrack())

    view_ref = args.CONCEPTS.view.Parse()
    view_name = util.GetViewName(
        view_ref.catalogsId,
        view_ref.namespacesId,
        view_ref.viewsId,
        project_id=view_ref.projectsId,
    )

    return client.projects_catalogs_namespaces_views.GetIamPolicy(
        messages.BiglakeProjectsCatalogsNamespacesViewsGetIamPolicyRequest(
            resource=view_name,
            options_requestedPolicyVersion=iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION,
        )
    )
