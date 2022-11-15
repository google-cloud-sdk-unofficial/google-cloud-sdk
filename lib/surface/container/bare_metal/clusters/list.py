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
"""Command to list all clusters in the Anthos on bare metal API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import bare_metal_clusters
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.bare_metal import constants
from googlecloudsdk.command_lib.container.bare_metal import flags

_EXAMPLES = """
To lists all clusters managed in location ``us-west1'', run:

$ {command} --location=us-west1
"""


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Anthos clusters on bare metal."""
  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Gathers command line arguments for the list command."""
    flags.AddLocationResourceArg(parser, 'to list')
    parser.display_info.AddFormat(constants.BARE_METAL_CLUSTERS_FORMAT)

  def Run(self, args):
    """Runs the list command.

    Args:
      args: Arguments received from command line.

    Returns:
      The resources listed by the service.
    """
    location_ref = args.CONCEPTS.location.Parse()
    client = bare_metal_clusters.ClustersClient()
    return client.List(location_ref, limit=args.limit, page_size=args.page_size)
