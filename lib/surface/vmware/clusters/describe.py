# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""'vmware clusters describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.clusters import ClustersClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe a VMware Engine cluster."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddClusterArgToParser(parser, positional=True)

  def Run(self, args):
    cluster = args.CONCEPTS.cluster.Parse()
    client = ClustersClient()
    return client.Get(cluster)


Describe.detailed_help = {
    'DESCRIPTION':
        """
          Describe a cluster in a VMware Engine private cloud.
        """,
    'EXAMPLES':
        """
          To describe a cluster called ``my-cluster'' in private cloud ``my-privatecloud'' and zone ``us-west2-a'', run:

            $ {command} my-cluster --location=us-west2-a --project=my-project --privatecloud=my-privatecloud

            Or:

            $ {command} my-cluster --privatecloud=my-privatecloud

           In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}
