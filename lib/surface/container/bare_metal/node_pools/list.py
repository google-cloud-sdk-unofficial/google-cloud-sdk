# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to list node pools in an Anthos cluster on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import bare_metal_node_pools as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.bare_metal import constants
from googlecloudsdk.command_lib.container.bare_metal import flags


_EXAMPLES = """
To list all node pools in a cluster named ``my-cluster''
managed in location ``us-west1'', run:

$ {command} --cluster=my-cluster --location=us-west1
"""


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List node pools in an Anthos cluster on bare metal."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    flags.AddClusterResourceArg(parser, 'to list', positional=False)
    parser.display_info.AddFormat(constants.BARE_METAL_NODE_POOLS_FORMAT)

  def Run(self, args):
    """Runs the list command."""
    cluster_ref = args.CONCEPTS.cluster.Parse()
    client = apis.NodePoolsClient()
    return client.List(cluster_ref, args.page_size)
