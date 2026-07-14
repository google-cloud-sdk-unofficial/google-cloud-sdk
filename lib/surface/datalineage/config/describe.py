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
"""Command to describe Data Lineage configuration."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datalineage import flags
from googlecloudsdk.command_lib.datalineage import util


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Describe Data Lineage configuration.

  ## EXAMPLES

  To describe the configuration for the current project, run:

        $ {command}

  To describe the configuration for the project ``my-project'', run:

        $ {command} --project=my-project

  To describe the configuration for the folder ``123456'', run:

        $ {command} --folder=123456

  To describe the configuration for the organization ``789012'', run:

        $ {command} --organization=789012
  """

  @classmethod
  def Args(cls, parser):
    """Adds command-specific args."""
    flags.AddParentArgs(parser)

  def Run(self, args):
    """Runs the describe command."""
    client = util.GetClient()
    messages = util.GetMessages()
    resource_name = util.GetConfigResourceName(args)

    if args.folder:
      request = messages.DatalineageFoldersLocationsConfigGetRequest(
          name=resource_name
      )
      return client.folders_locations_config.Get(request)
    elif args.organization:
      request = messages.DatalineageOrganizationsLocationsConfigGetRequest(
          name=resource_name
      )
      return client.organizations_locations_config.Get(request)
    else:
      request = messages.DatalineageProjectsLocationsConfigGetRequest(
          name=resource_name
      )
      return client.projects_locations_config.Get(request)
