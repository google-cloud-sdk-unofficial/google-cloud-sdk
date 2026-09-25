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
"""Command to describe an App Topology domain schema."""

from googlecloudsdk.api_lib.app_topology import domains as domains_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app_topology import resource_args


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Describe(base.DescribeCommand):
  """Describe the schema for an App Topology domain.

  Displays the node types, edge types, and supported property schemas available
  within the specified topology domain.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': (
          """\
          To describe the schema for the `SRE` domain in the default global location:

            $ {command} SRE

          To describe the schema for a domain in an explicit location:

            $ {command} SRE --location=global
          """
      ),
  }

  @staticmethod
  def Args(parser):
    """Registers command-line flags and arguments for domains schema describe."""
    resource_args.AddDomainResourceArg(parser, verb='whose schema to describe')

  def Run(self, args):
    """Executes the domains schema describe command.

    Args:
      args: argparse.Namespace, The parsed command-line arguments.

    Returns:
      messages.Schema: The domain schema metadata message.
    """
    client = domains_api.DomainsClient()
    domain_ref = args.CONCEPTS.domain.Parse()
    base_name = domain_ref.RelativeName().rstrip('/')
    parts = base_name.split('/')
    # Domain resource has 6 path segments: projects/*/locations/*/domains/*
    # Schema subresource has 7 segments: projects/*/locations/*/domains/*/schema
    # Checking count avoids collisions when domain is named 'schema'.
    if len(parts) == 6:
      schema_name = f'{base_name}/schema'
    else:
      schema_name = base_name
    return client.GetSchema(name=schema_name)
