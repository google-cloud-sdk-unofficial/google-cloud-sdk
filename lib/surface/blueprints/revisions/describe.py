# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Display details of a revision."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.blueprints import blueprints_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.blueprints import error_handling
from googlecloudsdk.command_lib.blueprints import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.DescribeCommand):
  """Display details of a revision."""

  detailed_help = {
      'EXAMPLES': ("""
        Retrieve information about a revision:

          $ {command} projects/my-project/locations/us-central1/deployments/\
my-deployment/revisions/r-0284ac1d-8127-47c0-809b-1b000edbe77d
      """)
  }

  @staticmethod
  def Args(parser):
    resource_args.AddRevisionResourceArg(
        parser,
        'the revision to describe.')

  def Epilog(self, resources_were_displayed):
    """Called after resources are displayed if the default format was used.

    Args:
      resources_were_displayed: True if resources were displayed.
    """

    messages = blueprints_util.GetMessagesModule()

    if (resources_were_displayed and self.revision_resource is not None and
        self.revision_resource.state ==
        messages.Revision.StateValueValuesEnum.FAILED):
      error_handling.RevisionFailed(self.revision_resource)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The resulting Revision resource.
    """
    revision_ref = args.CONCEPTS.revision.Parse()
    revision_full_name = revision_ref.RelativeName()

    existing_revision = blueprints_util.GetRevision(revision_full_name)

    # Save this for the Epilog to use.
    self.revision_resource = existing_revision

    return existing_revision
