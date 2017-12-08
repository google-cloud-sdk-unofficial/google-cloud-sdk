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

"""deployments stop command."""
from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import dm_v2_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

# Number of seconds (approximately) to wait for stop operation to complete.
OPERATION_TIMEOUT = 20 * 60  # 20 mins


class Stop(base.Command):
  """Stop a pending or running deployment update or creation.

  This command will stop a currently running or pending operation on
  a deployment.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To stop a running operation on a deployment, run:

            $ {command} my-deployment

          To issue a stop command without waiting for the operation to complete, run:

            $ {command} my-deployment --async
          """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        '--async',
        help='Return immediately and print information about the Operation in '
        'progress rather than waiting for the Operation to complete. '
        '(default=False)',
        default=False,
        action='store_true')

    parser.add_argument('deployment_name', help='Deployment name.')

  def Run(self, args):
    """Run 'deployments stop'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      If --async=true, returns Operation to poll.
      Else, returns boolean indicating whether stop operation succeeded.

    Raises:
      HttpException: An http error response was received while executing api
          request.
      ToolException: The stop operation encountered an error.
    """
    client = self.context['deploymentmanager-client']
    messages = self.context['deploymentmanager-messages']
    project = properties.VALUES.core.project.Get(required=True)

    # Get the fingerprint from the deployment to stop.
    try:
      current_deployment = client.deployments.Get(
          messages.DeploymentmanagerDeploymentsGetRequest(
              project=project,
              deployment=args.deployment_name
          )
      )
      # If no fingerprint is present, default to an empty fingerprint.
      # This empty default can be removed once the fingerprint change is
      # fully implemented and all deployments have fingerprints.
      fingerprint = current_deployment.fingerprint or ''
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(dm_v2_util.GetError(error))

    try:
      operation = client.deployments.Stop(
          messages.DeploymentmanagerDeploymentsStopRequest(
              project=project,
              deployment=args.deployment_name,
              deploymentsStopRequest=messages.DeploymentsStopRequest(
                  fingerprint=fingerprint,
              ),
          )
      )
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(dm_v2_util.GetError(error))
    if args.async:
      return operation
    else:
      op_name = operation.name
      try:
        dm_v2_util.WaitForOperation(op_name, project, self.context, 'stop',
                                    OPERATION_TIMEOUT)
        log.status.Print('Stop operation ' + op_name
                         + ' completed successfully.')
      except exceptions.ToolException:
        # Operation timed out or had errors. Print this warning, then still
        # show whatever operation can be gotten.
        log.error('Stop operation ' + op_name
                  + ' has errors or failed to complete within '
                  + str(OPERATION_TIMEOUT) + ' seconds.')
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(dm_v2_util.GetError(error))
      try:
        # Fetch a list of the stopped resources.
        response = client.resources.List(
            messages.DeploymentmanagerResourcesListRequest(
                project=project,
                deployment=args.deployment_name,
            )
        )
        # TODO(user): Pagination
        return response.resources if response.resources else []
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(dm_v2_util.GetError(error))
