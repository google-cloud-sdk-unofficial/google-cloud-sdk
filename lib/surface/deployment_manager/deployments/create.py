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

"""deployments create command."""

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import dm_v2_util
from googlecloudsdk.api_lib.deployment_manager import importer
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

# Number of seconds (approximately) to wait for create operation to complete.
OPERATION_TIMEOUT = 20 * 60  # 20 mins


class Create(base.Command):
  """Create a deployment.

  This command inserts (creates) a new deployment based on a provided config
  file.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To create a new deployment, run:

            $ {command} my-deployment --config config.yaml --description "My deployment"

          To preview a deployment without actually creating resources, run:

            $ {command} my-new-deployment --config config.yaml --preview

          To instantiate a deployment that has been previewed, issue an update command for that deployment without specifying a config file.
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
        dest='async',
        default=False,
        action='store_true')

    parser.add_argument('deployment_name', help='Deployment name.')

    parser.add_argument(
        '--config',
        help='Filename of config which specifies resources to deploy.',
        dest='config',
        required=True)

    parser.add_argument(
        '--properties',
        type=arg_parsers.ArgDict(),
        help='A comma seperated, key=value, map '
        'to be used when deploying a template file directly.',
        dest='properties')

    parser.add_argument(
        '--description',
        help='Optional description of the deployment to insert.',
        dest='description')

    parser.add_argument(
        '--preview',
        help='Preview the requested create without actually instantiating the '
        'underlying resources. (default=False)',
        dest='preview',
        default=False,
        action='store_true')

  def Collection(self):
    return 'deploymentmanager.resources_and_outputs'

  def Format(self, args):
    return self.ListFormat(args)

  def Epilog(self, resources_were_displayed):
    """Called after resources are displayed if the default format was used.

    Args:
      resources_were_displayed: True if resources were displayed.
    """
    if not resources_were_displayed:
      log.status.Print('No resources or outputs found in your deployment.')

  def Run(self, args):
    """Run 'deployments create'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      If --async=true, returns Operation to poll.
      Else, returns a struct containing the list of resources and list of
        outputs in the deployment.

    Raises:
      HttpException: An http error response was received while executing api
          request.
      ToolException: Config file could not be read or parsed, or the deployment
          creation operation encountered an error.
    """
    client = self.context['deploymentmanager-client']
    messages = self.context['deploymentmanager-messages']
    project = properties.VALUES.core.project.Get(required=True)

    deployment = messages.Deployment(
        name=args.deployment_name,
        target=importer.BuildTargetConfig(
            messages, args.config, args.properties),
    )
    if args.description:
      deployment.description = args.description

    try:
      operation = client.deployments.Insert(
          messages.DeploymentmanagerDeploymentsInsertRequest(
              project=project,
              deployment=deployment,
              preview=args.preview,
          )
      )
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(dm_v2_util.GetError(error))
    if args.async:
      return operation
    else:
      op_name = operation.name
      try:
        dm_v2_util.WaitForOperation(op_name, project, self.context, 'create',
                                    OPERATION_TIMEOUT)
        log.status.Print('Create operation ' + op_name
                         + ' completed successfully.')
      except exceptions.ToolException:
        # Operation timed out or had errors. Print this warning, then still
        # show whatever operation can be gotten.
        log.error('Create operation ' + op_name
                  + ' has errors or failed to complete within '
                  + str(OPERATION_TIMEOUT) + ' seconds.')
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(dm_v2_util.GetError(error))

      return dm_v2_util.FetchResourcesAndOutputs(client, messages, project,
                                                 args.deployment_name)
