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

"""deployments describe command."""

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import dm_v2_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties


class _Results(object):
  """Encapsulate results into a single object to fit the Run() model."""

  def __init__(self, deployment, resources):
    self.deployment = deployment
    self.resources = resources


class Describe(base.DescribeCommand):
  """Provide information about a deployment.

  This command prints out all available details about a deployment.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To display information about a deployment, run:

            $ {command} my-deployment
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
    parser.add_argument('deployment_name', help='Deployment name.')

  def Collection(self):
    return 'deploymentmanager.deployments'

  def Format(self, unused_args):
    """No need to list the id fields by default."""
    return ('default(deployment.name, deployment.id, deployment.fingerprint, '
            'deployment.insertTime, deployment.manifest.basename(), '
            'deployment.operation.operationType, deployment.operation.name, '
            'deployment.operation.progress, deployment.operation.status, '
            'deployment.operation.user, deployment.operation.endTime, '
            'deployment.operation.startTime, deployment.operation.error, '
            'resources[].name, resources[].type, '
            'resources[].update.state.yesno(no="COMPLETED"))')

  def Run(self, args):
    """Run 'deployments describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The requested Deployment.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    client = self.context['deploymentmanager-client']
    messages = self.context['deploymentmanager-messages']
    project = properties.VALUES.core.project.Get(required=True)

    try:
      deployment = client.deployments.Get(
          messages.DeploymentmanagerDeploymentsGetRequest(
              project=project, deployment=args.deployment_name))
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(dm_v2_util.GetError(error))

    # Get resources belonging to the deployment to display
    project = properties.VALUES.core.project.Get(required=True)
    try:
      response = client.resources.List(
          messages.DeploymentmanagerResourcesListRequest(
              project=project, deployment=deployment.name))
      resources = response.resources
    except apitools_exceptions.HttpError:
      # Couldn't get resources, skip adding them to the table.
      # TODO(user): Why not raise HTTP exception here?
      resources = None

    return _Results(deployment, resources)
