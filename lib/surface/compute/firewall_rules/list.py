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
"""Command for listing firewall rules."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.firewall_rules import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class List(base_classes.GlobalLister):
  """List Google Compute Engine firewall rules."""

  @property
  def service(self):
    return self.compute.firewalls

  @property
  def resource_type(self):
    return 'firewalls'


List.detailed_help = base_classes.GetGlobalListerHelp('firewall rules')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """List Google Compute Engine firewall rules."""

  def Run(self, args):
    log.status.Print(flags.LIST_NOTICE)

    return super(ListAlpha, self).Run(args)

  def Collection(self):
    return 'compute.firewalls.alpha'


RESOURCE_TYPE = 'firewall rules'

ListAlpha.detailed_help = {
    'brief':
        'List Google Compute Engine ' + RESOURCE_TYPE,
    'DESCRIPTION':
        """\
          *{{command}}* displays all Google Compute Engine {0} in a project.
          """.format(RESOURCE_TYPE),
    'EXAMPLES':
        """\
To list all {0} in a project in table form, run:

    $ {{command}}

To list the URIs of all {0} in a project, run:

    $ {{command}} --uri

To list all fields of all {0} in a project, run:

    $ {{command}} --format="{1}"
""".format(RESOURCE_TYPE, flags.LIST_WITH_ALL_FIELDS_FORMAT)
}
