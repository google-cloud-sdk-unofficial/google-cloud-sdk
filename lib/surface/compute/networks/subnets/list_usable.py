# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command for list subnetworks which the current user has permission to use."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListUsableSubnets(base.ListCommand):
  """List subnetworks which the current user has permission to use."""

  @staticmethod
  def _EnableComputeApi():
    return properties.VALUES.compute.use_new_list_usable_subnets_api.GetBool()

  @staticmethod
  def Args(parser):
    if ListUsableSubnets._EnableComputeApi():
      display_format = 'table({fields})'.format(fields=','.join([
          'subnetwork.segment(-5):label=PROJECT',
          'subnetwork.segment(-3):label=REGION',
          'network.segment(-1):label=NETWORK',
          'subnetwork.segment(-1):label=SUBNET',
          'ipCidrRange:label=RANGE',
      ]))
    else:
      display_format = 'table({fields})'.format(fields=','.join([
          'resource.selfLink.segment(-5):label=PROJECT',
          'resource.region.segment(-1):label=REGION',
          'resource.network.segment(-1):label=NETWORK',
          'resource.selfLink.segment(-1):label=SUBNET',
          'resource.ipCidrRange:label=RANGE',
      ]))
    parser.display_info.AddFormat(display_format)

  def Collection(self):
    return 'compute.subnetworks'

  def GetUriFunc(self):
    def _GetUri(search_result):
      return ''.join([
          p.value.string_value
          for p
          in search_result.resource.additionalProperties
          if p.key == 'selfLink'])
    return _GetUri

  def Run(self, args):
    enable_compute_api = ListUsableSubnets._EnableComputeApi()
    if enable_compute_api:
      return self._CallComputeApi()
    else:
      log.warn(
          'The behavior of this command will change in the near future to only '
          'return the usable subnets in the current project (the default or '
          'the --project flag). You can dismiss this warning '
          'and switch to the new behavior now by running '
          '"gcloud config set compute/use_new_list_usable_subnets_api True".')
      return self._CallNconApi()

  def _CallComputeApi(self):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages
    request = messages.ComputeSubnetworksListUsableRequest(
        project=properties.VALUES.core.project.Get(required=True))
    return list_pager.YieldFromList(
        client.apitools_client.subnetworks,
        request,
        method='ListUsable',
        batch_size_attribute='maxResults',
        batch_size=500,
        field='items')

  def _CallNconApi(self):
    messages = apis.GetMessagesModule('cloudresourcesearch', 'v1')
    client = apis.GetClientInstance('cloudresourcesearch', 'v1')
    request = messages.CloudresourcesearchResourcesSearchRequest(
        query='@type="type.googleapis.com/compute.Subnetwork"'
              ' withPermission(compute.subnetworks.use)')
    return list_pager.YieldFromList(
        client.resources,
        request,
        method='Search',
        batch_size_attribute='pageSize',
        batch_size=100,
        field='results')

ListUsableSubnets.detailed_help = {
    'brief': 'List subnetworks which the current user has permission to use.',
    'DESCRIPTION': """\
        *{command}* is used to list subnetworks which the current user has permission to use.
        """,
    'EXAMPLES': """\
          $ {command}
        """,
}
