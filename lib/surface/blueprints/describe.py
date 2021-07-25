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
"""Display details of a deployment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.blueprints import blueprints_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.blueprints import error_handling
from googlecloudsdk.command_lib.blueprints import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.DescribeCommand):
  """Display details of a deployment."""

  detailed_help = {
      'EXAMPLES': ("""
        Retrieve information about a deployment:

          $ {command} my-deployment
      """)
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDeploymentResourceArg(
        parser,
        'the deployment to describe.')

  def Epilog(self, resources_were_displayed):
    """Called after resources are displayed if the default format was used.

    Args:
      resources_were_displayed: True if resources were displayed.
    """

    messages = blueprints_util.GetMessagesModule()

    if (resources_were_displayed and self.deployment_resource is not None and
        self.deployment_resource.state ==
        messages.Deployment.StateValueValuesEnum.FAILED):
      error_handling.DeploymentFailed(self.deployment_resource)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The resulting Deployment resource.
    """
    deployment_ref = args.CONCEPTS.deployment.Parse()
    deployment_full_name = deployment_ref.RelativeName()

    existing_deployment = blueprints_util.GetDeployment(deployment_full_name)

    # Save this for the Epilog to use.
    self.deployment_resource = existing_deployment

    return existing_deployment
