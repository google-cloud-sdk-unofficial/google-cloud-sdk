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
"""Command to generate resource topology graph."""

import re

from googlecloudsdk.api_lib.app_topology import topologies as topologies_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.app_topology import flags
from googlecloudsdk.command_lib.app_topology import resource_args


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Generate(base.Command):
  """Generate a resource topology graph.

  Queries the App Topology service to construct and return a directed graph of
  discovered cloud resources and their relationships across the specified
  domains.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': (
          """\
          To generate a resource topology graph for the `SRE` domain:

            $ {command} --domains=SRE

          To generate a topology graph with an inline pattern filter:

            $ {command} --domains=SRE,DEVOPS \
                --pattern='{"starting_node": {"label_matcher_expr": "AppHub"}'

          To generate a topology graph using a pattern filter from a file:

            $ {command} --domains=SRE --pattern-file=path/to/pattern.yaml
          """
      ),
  }

  @staticmethod
  def Args(parser):
    """Registers flags and arguments for resources-graph generate."""
    # Remove standard Calliope client-side --filter flag to avoid conflicting
    # with backend GraphPattern --pattern / --pattern-file flags.
    base.FILTER_FLAG.RemoveFromParser(parser)
    resource_args.AddLocationResourceArg(parser, verb='to query topology in')
    flags.AddDomainsFlag(parser, required=True)
    flags.AddPatternGroup(parser)
    parser.display_info.AddFormat('yaml')

  def Run(self, args):
    """Executes the resources-graph generate command.

    Args:
      args: argparse.Namespace, The parsed command-line arguments.

    Returns:
      dict: The normalized resource topology graph.

    Raises:
      exceptions.InvalidArgumentException: If no valid non-empty domains are
      provided.
    """
    client = topologies_api.DiscoveredResourcesTopologiesClient()
    location_ref = args.CONCEPTS.location.Parse()
    topology_name = f'{location_ref.RelativeName()}/discoveredResourcesTopology'

    domains = []
    seen = set()
    for d in args.domains:
      # Strip leading and trailing whitespace/slashes (e.g. ' /SRE/ ').
      d = d.strip().strip('/')
      if not d:
        continue
      # Strip leading full URI schemes, custom proxy/gateway paths, or API
      # version prefixes (e.g. 'https://custom-gateway.internal/proxy/v1/...',
      # 'https://apptopology...'). # gcloud-disable-gdu-domain
      if (
          d.startswith('http://')
          or d.startswith('https://')
          or d.startswith('//')
      ):
        match = re.search(r'projects/[^/]+/locations/[^/]+/domains/[^/]+', d)
        if match:
          d = match.group(0)
        elif '/domains/' in d:
          d = d[d.index('domains/') :]
        else:
          d = re.sub(r'^(https?://[^/]+/(?:v[0-9a-zA-Z_]+/)?|//[^/]+/)', '', d)
      d = d.strip('/')
      if d.startswith('domains/'):
        d = d[len('domains/') :]
      # Handle relative paths starting with 'locations/'
      # (e.g. 'locations/global/domains/SRE' -> 'projects/...').
      if d.startswith('locations/'):
        project = location_ref.projectsId
        d = f'projects/{project}/{d}'
      # Handle bare domain names (e.g. 'SRE' -> '{location_ref}/domains/SRE').
      elif not d.startswith('projects/'):
        d = f'{location_ref.RelativeName()}/domains/{d}'
      # Deduplicate domains while preserving user order.
      if d not in seen:
        seen.add(d)
        domains.append(d)

    if not domains:
      raise exceptions.InvalidArgumentException(
          '--domains', 'At least one non-empty domain name must be specified.'
      )

    return client.Generate(
        name=topology_name,
        domains=domains,
        pattern=args.pattern,
        pattern_file=args.pattern_file,
    )
