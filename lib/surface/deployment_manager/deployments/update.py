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

"""deployments update command."""

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.deployment_manager import dm_v2_util
from googlecloudsdk.api_lib.deployment_manager import importer
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import apis as core_apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

# Number of seconds (approximately) to wait for update operation to complete.
OPERATION_TIMEOUT = 20 * 60  # 20 mins


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update a deployment based on a provided config file.

  This command will update a deployment with the new config file provided.
  Different policies for create, update, and delete policies can be specified.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To update an existing deployment with a new config file, run:

            $ {command} my-deployment --config new_config.yaml

          To preview an update to an existing deployment without actually modifying the resources, run:

            $ {command} my-deployment --config new_config.yaml --preview

          To apply an update that has been previewed, provide the name of the previewed deployment, and no config file:

            $ {command} my-deployment

          To specify different create, update, or delete policies, include any subset of the following flags;

            $ {command} my-deployment --config new_config.yaml --create-policy ACQUIRE --delete-policy ABANDON

          To perform an update without waiting for the operation to complete, run:

            $ {command} my-deployment --config new_config.yaml --async
          """,
  }

  @staticmethod
  def Args(parser, version=base.ReleaseTrack.GA):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
      version: The version this tool is running as. base.ReleaseTrack.GA
          is the default.
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

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--config',
        help='Filename of config which specifies resources to deploy. '
        'Required unless launching an already-previewed update to this '
        'deployment.',
        dest='config')

    if version in [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]:
      group.add_argument(
          '--manifest-id',
          help='Manifest Id of a previous deployment. '
          'This flag cannot be used with --config.',
          dest='manifest_id')

    parser.add_argument(
        '--properties',
        type=arg_parsers.ArgDict(),
        help='A comma seperated, key=value, map '
        'to be used when deploying a template file directly.',
        dest='properties')

    parser.add_argument(
        '--preview',
        help='Preview the requested update without making any changes to the'
        'underlying resources. (default=False)',
        dest='preview',
        default=False,
        action='store_true')

    v2_messages = core_apis.GetMessagesModule('deploymentmanager', 'v2')
    parser.add_argument(
        '--create-policy',
        help='Create policy for resources that have changed in the update. '
        'Can be CREATE_OR_ACQUIRE (default) or ACQUIRE.',
        dest='create_policy',
        default='CREATE_OR_ACQUIRE',
        choices=(v2_messages.DeploymentmanagerDeploymentsUpdateRequest
                 .CreatePolicyValueValuesEnum.to_dict().keys()))

    parser.add_argument(
        '--delete-policy',
        help='Delete policy for resources that have changed in the update. '
        'Can be DELETE (default) or ABANDON.',
        dest='delete_policy',
        default='DELETE',
        choices=(v2_messages.DeploymentmanagerDeploymentsUpdateRequest
                 .DeletePolicyValueValuesEnum.to_dict().keys()))

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
    """Run 'deployments update'.

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
    )

    if args.config:
      deployment.target = importer.BuildTargetConfig(
          messages, args.config, args.properties)
    elif (self.ReleaseTrack() in [base.ReleaseTrack.ALPHA,
                                  base.ReleaseTrack.BETA]
          and args.manifest_id):
      deployment.target = importer.BuildTargetConfigFromManifest(
          client, messages, project, args.deployment_name, args.manifest_id,
          args.properties)
    # Get the fingerprint from the deployment to update.
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
      deployment.fingerprint = current_deployment.fingerprint or ''
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(dm_v2_util.GetError(error))

    try:
      operation = client.deployments.Update(
          messages.DeploymentmanagerDeploymentsUpdateRequest(
              deploymentResource=deployment,
              project=project,
              deployment=args.deployment_name,
              preview=args.preview,
              createPolicy=(messages.DeploymentmanagerDeploymentsUpdateRequest
                            .CreatePolicyValueValuesEnum(args.create_policy)),
              deletePolicy=(messages.DeploymentmanagerDeploymentsUpdateRequest
                            .DeletePolicyValueValuesEnum(args.delete_policy)),
          )
      )
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(dm_v2_util.GetError(error))
    if args.async:
      return operation
    else:
      op_name = operation.name
      try:
        dm_v2_util.WaitForOperation(op_name, project, self.context, 'update',
                                    OPERATION_TIMEOUT)
        log.status.Print('Update operation ' + op_name
                         + ' completed successfully.')
      except exceptions.ToolException:
        # Operation timed out or had errors. Print this warning, then still
        # show whatever operation can be gotten.
        log.error('Update operation ' + op_name
                  + ' has errors or failed to complete within '
                  + str(OPERATION_TIMEOUT) + ' seconds.')
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(dm_v2_util.GetError(error))

      return dm_v2_util.FetchResourcesAndOutputs(client, messages, project,
                                                 args.deployment_name)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBETA(Update):
  """Update a deployment based on a provided config file.

  This command will update a deployment with the new config file provided.
  Different policies for create, update, and delete policies can be specified.
  """

  @staticmethod
  def Args(parser):
    Update.Args(parser, version=base.ReleaseTrack.BETA)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateALPHA(Update):
  """Update a deployment based on a provided config file.

  This command will update a deployment with the new config file provided.
  Different policies for create, update, and delete policies can be specified.
  """

  @staticmethod
  def Args(parser):
    Update.Args(parser, version=base.ReleaseTrack.ALPHA)
