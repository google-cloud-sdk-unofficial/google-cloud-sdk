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
"""Command to get the IAM policy for a BigLake Hive catalog database."""

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for a BigLake Hive catalog database."""

  detailed_help = {
      'DESCRIPTION': 'Gets the IAM policy for a BigLake Hive catalog database.',
      'EXAMPLES': (
          """\
          To get the IAM policy for the catalog `my-catalog` and database `my-database` run:

            $ {command} my-database --catalog=my-catalog
          """
      ),
  }

  # Iceberg and Hive share the same get_iam_policy method, but Iceberg has
  # namespaces while Hive has databases. Namespace is the correct term for the
  # path in the request, so we use the namespace resource arg here.
  @staticmethod
  def Args(parser):
    flags.AddNamespaceResourceArg(
        parser, 'to get the IAM policy for', namespace_type='Hive'
    )
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = util.GetClientInstance(self.ReleaseTrack())
    messages = util.GetMessagesModule(self.ReleaseTrack())

    project = args.project or properties.VALUES.core.project.Get(required=True)
    namespace_name = (
        f'projects/{project}/catalogs/{args.catalog}/namespaces/{args.database}'
    )

    return client.projects_catalogs_namespaces.GetIamPolicy(
        messages.BiglakeProjectsCatalogsNamespacesGetIamPolicyRequest(
            resource=namespace_name
        )
    )
