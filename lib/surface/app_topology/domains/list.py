# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command to list App Topology domains."""

from googlecloudsdk.api_lib.app_topology import domains as domains_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app_topology import resource_args

_FORMAT = """
  table(
    name.scope("domains"):label=NAME
  )
"""


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List App Topology domains.

  Lists all topology domains registered in the specified location (defaults to
  'global').
  """

  detailed_help = {
      'DESCRIPTION': (
          '{description}\n\nLists all topology domains registered in the'
          ' specified location (defaults to "global").'
      ),
      'EXAMPLES': (
          """\
          To list all App Topology domains in the default global location:

            $ {command}

          To list all App Topology domains in a specific location:

            $ {command} --location=global

          To list all App Topology domains with their full resource URIs:

            $ {command} --uri
          """
      ),
  }

  @staticmethod
  def Args(parser):
    """Registers command-line flags and arguments for domains list."""
    resource_args.AddLocationResourceArg(parser, verb='to list domains for')
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(lambda r: r.name)

  def Run(self, args):
    """Executes the domains list command.

    Args:
      args: argparse.Namespace, The parsed command-line arguments.

    Returns:
      Generator: Yields Domain messages.
    """
    client = domains_api.DomainsClient()
    location_ref = args.CONCEPTS.location.Parse()
    parent = location_ref.RelativeName()
    return client.List(
        parent=parent, page_size=args.page_size, limit=args.limit
    )
