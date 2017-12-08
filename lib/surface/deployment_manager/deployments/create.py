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
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.deployment_manager import dm_base
from googlecloudsdk.command_lib.deployment_manager import dm_util
from googlecloudsdk.command_lib.deployment_manager import dm_write
from googlecloudsdk.command_lib.deployment_manager import flags
from googlecloudsdk.command_lib.util import labels_util
from googlecloudsdk.core import log

# Number of seconds (approximately) to wait for create operation to complete.
OPERATION_TIMEOUT = 20 * 60  # 20 mins


@base.UnicodeIsSupported
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
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
  def Args(parser, version=base.ReleaseTrack.GA):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
      version: The version this tool is running as. base.ReleaseTrack.GA
          is the default.
    """
    flags.AddAsyncFlag(parser)
    flags.AddDeploymentNameFlag(parser)
    flags.AddPropertiesFlag(parser)

    if version in [base.ReleaseTrack.ALPHA]:
      labels_util.AddCreateLabelsFlags(parser)
    parser.add_argument(
        '--description',
        help='Optional description of the deployment to insert.',
        dest='description')

    parser.add_argument(
        '--config',
        help='Filename of config which specifies resources to deploy.',
        dest='config',
        required=True)

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
      ConfigError: Config file could not be read or parsed, or the
          deployment creation operation encountered an error.
    """
    deployment = dm_base.GetMessages().Deployment(
        name=args.deployment_name,
        target=importer.BuildTargetConfig(
            dm_base.GetMessages(), args.config, args.properties),
    )
    if self.ReleaseTrack() in [base.ReleaseTrack.ALPHA]:
      label_dict = labels_util.GetUpdateLabelsDictFromArgs(args)
      label_entry = []
      if label_dict:
        label_entry = [dm_base.GetMessages().DeploymentLabelEntry(key=k,
                                                                  value=v)
                       for k, v in sorted(label_dict.iteritems())]
        deployment.labels = label_entry

    if args.description:
      deployment.description = args.description

    try:
      operation = dm_base.GetClient().deployments.Insert(
          dm_base.GetMessages().DeploymentmanagerDeploymentsInsertRequest(
              project=dm_base.GetProject(),
              deployment=deployment,
              preview=args.preview,
          )
      )
      # Fetch and print the latest fingerprint of the deployment.
      fingerprint = dm_v2_util.FetchDeploymentFingerprint(
          dm_base.GetClient(),
          dm_base.GetMessages(),
          dm_base.GetProject(),
          args.deployment_name)
      dm_util.PrintFingerprint(fingerprint)

    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, dm_v2_util.HTTP_ERROR_FORMAT)
    if args.async:
      return operation
    else:
      op_name = operation.name
      try:
        dm_write.WaitForOperation(op_name,
                                  operation_description='create',
                                  project=dm_base.GetProject(),
                                  timeout=OPERATION_TIMEOUT)
        log.status.Print('Create operation ' + op_name
                         + ' completed successfully.')
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(error, dm_v2_util.HTTP_ERROR_FORMAT)

      return dm_v2_util.FetchResourcesAndOutputs(dm_base.GetClient(),
                                                 dm_base.GetMessages(),
                                                 dm_base.GetProject(),
                                                 args.deployment_name)


@base.UnicodeIsSupported
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBETA(Create):
  """Create a deployment.

  This command inserts (creates) a new deployment based on a provided config
  file.
  """

  @staticmethod
  def Args(parser):
    Create.Args(parser, version=base.ReleaseTrack.BETA)


@base.UnicodeIsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateALPHA(Create):
  """Create a deployment.

  This command inserts (creates) a new deployment based on a provided config
  file.
  """

  @staticmethod
  def Args(parser):
    Create.Args(parser, version=base.ReleaseTrack.ALPHA)
