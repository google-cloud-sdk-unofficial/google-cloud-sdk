# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Command for deleting cross site networks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.interconnects.cross_site_networks import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.interconnects.cross_site_networks import flags
from googlecloudsdk.core import properties


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete Compute Engine cross site networks.

  *{command}* deletes Compute Engine cross site networks.
  """

  CROSS_SITE_NETWORK_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.CROSS_SITE_NETWORK_ARG = flags.CrossSiteNetworkArgument(plural=True)
    cls.CROSS_SITE_NETWORK_ARG.AddArgument(parser, operation_type='delete')

  def Collection(self):
    return 'compute.crossSiteNetworks'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    refs = self.CROSS_SITE_NETWORK_ARG.ResolveAsResource(args, holder.resources)
    project = properties.VALUES.core.project.GetOrFail()
    utils.PromptForDeletion(refs)

    requests = []
    for ref in refs:
      cross_site_network = client.CrossSiteNetwork(
          ref, project=project, compute_client=holder.client
      )
      requests.extend(
          cross_site_network.Delete(only_generate_request=True)
      )

    return holder.client.MakeRequests(requests)
