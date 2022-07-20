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
"""Command to list all clusters in the Anthos clusters on VMware API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.vmware import clusters as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.vmware import flags

_EXAMPLES = """
To lists all clusters managed in location ``us-west1'', run:

$ {command} --location=us-west1
"""


VMWARE_CLUSTERS_FORMAT = """
table(
  name.segment(5):label=NAME,
  name.segment(3):label=LOCATION,
  onPremVersion,
  adminClusterMembership.segment(5),
  state)
"""


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Anthos clusters on VMware."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(VMWARE_CLUSTERS_FORMAT)
    # parser.display_info.AddUriFunc(apis.GetClusterURI)
    flags.AddLocationResourceArg(parser)

  def Run(self, args):
    """Runs the list command."""
    location_ref = args.CONCEPTS.location.Parse()
    client = apis.ClustersClient()
    return client.List(location_ref, limit=args.limit, page_size=args.page_size)
