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
"""Delete a deployment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.blueprints import blueprints_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.blueprints import error_handling
from googlecloudsdk.command_lib.blueprints import flags
from googlecloudsdk.command_lib.blueprints import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.DeleteCommand):
  """Delete a deployment.

  This deletes a deployment and all of its child revisions.
  """

  detailed_help = {
      'EXAMPLES': ("""
        Delete a deployment:

          $ {command} my-deployment
      """)
  }

  @staticmethod
  def Args(parser):
    flags.AddAsyncFlag(parser)
    resource_args.AddDeploymentResourceArg(parser, 'the deployment to delete.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      In the case that args.async_ is True, a long-running operation, otherwise
        nothing is returned.
    """
    messages = blueprints_util.GetMessagesModule()
    deployment_ref = args.CONCEPTS.deployment.Parse()
    deployment_name = deployment_ref.Name()
    deployment_full_name = deployment_ref.RelativeName()

    message = ('You are about to delete deployment [{0}]\n'
               'Warning: If this is a clusterless deployment, the deployment '
               'will be deleted, but the underlying resources will be '
               'orphaned. Resource deletion and pruning is not implemented.')

    console_io.PromptContinue(
        message=message.format(deployment_name),
        cancel_on_no=True)

    op = blueprints_util.DeleteDeployment(deployment_full_name)
    log.status.Print('Delete request issued for: [{0}]'.format(deployment_name))

    if args.async_:
      log.status.Print('Check operation [{0}] for status.'.format(op.name))
      return op

    op_response = blueprints_util.WaitForDeleteDeploymentOperation(op)

    # Check if the deletion failed so that we can print helpful troubleshooting
    # information.
    response_dict = encoding.MessageToPyValue(op_response)
    if response_dict['state'] == str(
        messages.Deployment.StateValueValuesEnum.FAILED):
      try:
        deployment_resource = blueprints_util.GetDeployment(
            deployment_full_name)
        error_handling.DeploymentFailed(deployment_resource)
      except apitools_exceptions.HttpNotFoundError:
        # To have gotten here, it means that the deletion operation failed but
        # _also_ that we got a 404 when trying to fetch the deployment (which
        # would imply that the deployment _was_ deleted). This is likely only
        # possible due to a race condition. Performing another delete wouldn't
        # have an effect.
        pass

    return op_response
