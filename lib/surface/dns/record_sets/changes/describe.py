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

"""gcloud dns record-sets changes describe command."""

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resolvers


class Describe(base.DescribeCommand):
  """View the details of a change.

  This command displays the details of the specified change.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To display the details of a change, run:

            $ {command} change_id
          """,
  }

  @staticmethod
  def Args(parser):
    util.ZONE_FLAG.AddToParser(parser)
    parser.add_argument(
        'change_id', metavar='CHANGE_ID',
        help='The ID of the change you want details for.')

  def Run(self, args):
    dns = self.context['dns_client']
    resources = self.context['dns_resources']
    change_ref = resources.Parse(
        args.change_id,
        params={'managedZone': resolvers.FromArgument('--zone', args.zone)},
        collection='dns.changes')

    return dns.changes.Get(
        dns.MESSAGES_MODULE.DnsChangesGetRequest(
            project=change_ref.project,
            managedZone=change_ref.managedZone,
            changeId=change_ref.changeId))
