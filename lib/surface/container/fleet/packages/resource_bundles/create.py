# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command to create Resource Bundle."""

from googlecloudsdk.api_lib.container.fleet.packages import resource_bundles as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.packages import flags

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To create Resource Bundle ``cert-manager'' in ``us-central1'', run:

          $ {command} cert-manager --location=us-central1
        """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create Package Rollouts Resource Bundle."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddNameFlag(parser)
    flags.AddLocationFlag(parser)
    flags.AddDescriptionFlag(parser)

  def Run(self, args):
    """Run the create command."""
    client = apis.ResourceBundlesClient()
    project = flags.GetProject(args)
    location = flags.GetLocation(args)
    return client.Create(project=project, location=location, name=args.name)
