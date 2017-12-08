# Copyright 2016 Google Inc. All Rights Reserved.
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

"""types list command."""

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.deployment_manager import dm_v2_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deployment_manager import dm_base
from googlecloudsdk.command_lib.deployment_manager import dm_beta_base
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List types in a project.

  Prints a list of the available resource types.
  """

  detailed_help = {
      'EXAMPLES': """\
          To print out a list of all available type names, run:

            $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """Run 'types list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of types for this project.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    request = dm_base.GetMessages().DeploymentmanagerTypesListRequest(
        project=dm_base.GetProject())
    return dm_v2_util.YieldWithHttpExceptions(
        list_pager.YieldFromList(dm_base.GetClient().types, request,
                                 field='types', batch_size=args.page_size,
                                 limit=args.limit))

  def Collection(self):
    return 'deploymentmanager.types'

  def Epilog(self, resources_were_displayed):
    if not resources_were_displayed:
      log.status.Print('No types were found for your project!')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListALPHA(base.ListCommand):
  """Describe a type provider type."""

  detailed_help = {
      'EXAMPLES': """\
          To print out a list of all available type names, run:

            $ {command}

          If you only want the types for a specific provider, you can specify
          which one using --provider

            $ {command} --provider=PROVIDER
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('--provider', help='Type provider name.')

  def Run(self, args):
    """Run 'types list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of types for this project.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    type_provider_ref = dm_beta_base.GetResources().Parse(
        args.provider if args.provider else 'NOT_A_PROVIDER',
        collection='deploymentmanager.typeProviders')
    if not args.provider:
      type_providers = self.GetTypeProviders(type_provider_ref.project,
                                             args.page_size,
                                             args.limit)
    else:
      type_providers = [type_provider_ref.typeProvider]

    return dm_v2_util.YieldWithHttpExceptions(
        self.YieldTypes(type_providers,
                        type_provider_ref.project,
                        args.page_size,
                        args.limit))

  def GetTypeProviders(self, project, page_size, limit):
    request = (dm_beta_base.GetMessages().
               DeploymentmanagerTypeProvidersListRequest(
                   project=project))
    type_providers = []
    paginated_providers = dm_v2_util.YieldWithHttpExceptions(
        list_pager.YieldFromList(dm_beta_base.GetClient().typeProviders,
                                 request,
                                 field='typeProviders',
                                 batch_size=page_size,
                                 limit=limit))
    for type_provider in paginated_providers:
      type_providers.append(type_provider.name)

    return type_providers

  def YieldTypes(self, type_providers, project, page_size, limit):
    for type_provider in type_providers:
      request = (dm_beta_base.GetMessages().
                 DeploymentmanagerTypeProvidersListTypesRequest(
                     project=project,
                     typeProvider=type_provider))
      paginated_types = list_pager.YieldFromList(
          dm_beta_base.GetClient().typeProviders,
          request,
          method='ListTypes',
          field='types',
          batch_size=page_size,
          limit=limit)
      for t in paginated_types:
        yield {'type': t, 'provider': type_provider}

  def Format(self, unused_args):
    return 'table(type.name, provider)'
