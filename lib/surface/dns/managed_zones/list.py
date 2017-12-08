# Copyright 2014 Google Inc. All Rights Reserved.
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

"""gcloud dns managed-zones list command."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class List(base.ListCommand):
  """View the list of all your managed-zones.

  This command displays the list of your managed-zones.

  ## EXAMPLES

  To see the list of all managed-zones, run:

    $ {command}

  To see the list of first 10 managed-zones, run:

    $ {command} --limit=10
  """

  def Collection(self):
    return 'dns.managedZones'

  def GetUriFunc(self):
    def _GetUri(resource):
      return resources.REGISTRY.Create(
          self.Collection(), managedZone=resource.name).SelfLink()
    return _GetUri

  def Run(self, args):
    dns_client = apis.GetClientInstance('dns', 'v1')
    dns_messages = apis.GetMessagesModule('dns', 'v1')

    project_id = properties.VALUES.core.project.Get(required=True)

    return list_pager.YieldFromList(
        dns_client.managedZones,
        dns_messages.DnsManagedZonesListRequest(project=project_id),
        limit=args.limit, field='managedZones')
