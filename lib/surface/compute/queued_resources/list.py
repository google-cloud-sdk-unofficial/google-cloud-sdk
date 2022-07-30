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
"""Command for listing queued resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute.queued_resources import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """\
        {command} displays all Compute Engine queued resources in a project
        in given zones.
      """,
    'EXAMPLES':
        """\
        To list all queued resources in a project in table form in specified zones, run:

        $ {command} --zones=us-central1-a,us-central1-b

        To list the URIs of all queued resources in a project in specified zones, run:

        $ {command} --zones=us-central1-a,us-central1-b --uri
    """
}


class List(base.ListCommand):
  """List Compute Engine queued resources."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddOutputFormat(parser)
    parser.display_info.AddUriFunc(utils.MakeGetUriFunc())
    # TODO(b/212438138) Use lister.AddZonalListerArgs(parser).
    parser.add_argument(
        '--zones',
        metavar='ZONE',
        help='Only resources from the given zones are queried.',
        type=arg_parsers.ArgList(min_length=1),
        required=True,
        completer=compute_completers.ZonesCompleter,
        default=[])

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseZonalFlags(args, holder.resources)

    list_implementation = lister.ZonalLister(
        client, client.apitools_client.zoneQueuedResources)

    return lister.Invoke(request_data, list_implementation)
