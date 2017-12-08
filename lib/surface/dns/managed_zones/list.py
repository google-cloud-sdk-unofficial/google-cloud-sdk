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

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import list_printer
from googlecloudsdk.core import properties
from googlecloudsdk.core import remote_completion
from googlecloudsdk.core import resources
from googlecloudsdk.third_party.apitools.base.py import list_pager


class List(base.Command):
  """View the list of all your managed-zones.

  This command displays the list of your managed-zones.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To see the list of all managed-zones, run:

            $ {command}

          To see the list of first 10 managed-zones, run:

            $ {command} --limit=10
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--limit', default=None, required=False, type=int,
        help='Maximum number of managed-zones to list.')

  @staticmethod
  def GetRef(item):
    instance_ref = resources.Create('dns.managedZones',
                                    managedZone=item.name)
    return instance_ref.SelfLink()

  def Run(self, args):
    dns_client = self.context['dns_client']
    dns_messages = self.context['dns_messages']

    project_id = properties.VALUES.core.project.Get(required=True)
    remote_completion.SetGetInstanceFun(self.GetRef)

    return list_pager.YieldFromList(
        dns_client.managedZones,
        dns_messages.DnsManagedZonesListRequest(project=project_id),
        limit=args.limit, field='managedZones')

  @util.HandleHttpError
  def Display(self, args, result):
    instance_refs = []
    items = remote_completion.Iterate(result, instance_refs, self.GetRef)
    list_printer.PrintResourceList('dns.managedZones', items)
    cache = remote_completion.RemoteCompletion()
    cache.StoreInCache(instance_refs)
