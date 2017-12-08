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
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
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


def TypeProviderClient():
  """Return a Type Provider client specially suited for listing types.

  Listing types requires many API calls, some of which may fail due to bad
  user configurations which show up as errors that are retryable. We can
  alleviate some of the latency and usability issues this causes by tuning
  the client.

  Returns:
    A Type Provider API client.
  """
  main_client = dm_beta_base.GetClient()
  main_client.num_retries = 2
  return main_client.typeProviders


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
    self.page_size = args.page_size
    self.limit = args.limit
    self.project = type_provider_ref.project

    if not args.provider:
      type_providers = self._GetTypeProviders()
    else:
      type_providers = [type_provider_ref.typeProvider]

    return dm_v2_util.YieldWithHttpExceptions(
        self._YieldPrintableTypesOrErrors(type_providers))

  def _GetTypeProviders(self):
    request = (dm_beta_base.GetMessages().
               DeploymentmanagerTypeProvidersListRequest(
                   project=self.project))
    providers = dm_v2_util.YieldWithHttpExceptions(
        list_pager.YieldFromList(TypeProviderClient(),
                                 request,
                                 field='typeProviders',
                                 batch_size=self.page_size,
                                 limit=self.limit))

    return [provider.name for provider in providers]

  def _YieldPrintableTypesOrErrors(self, type_providers):
    """Yield dicts of types list, provider, and (optionally) an error message.

    Args:
      type_providers: A list of Type Provider names to grab Type Info
        messages for.

    Yields:
      A dict object with a list of types, a type provider, and (optionally)
      an error message for display.

    """
    for type_provider in type_providers:
      request = (dm_beta_base.GetMessages().
                 DeploymentmanagerTypeProvidersListTypesRequest(
                     project=self.project,
                     typeProvider=type_provider))
      try:
        paginated_types = dm_v2_util.YieldWithHttpExceptions(
            list_pager.YieldFromList(TypeProviderClient(),
                                     request,
                                     method='ListTypes',
                                     field='types',
                                     batch_size=self.page_size,
                                     limit=self.limit))
        yield {'types': list(paginated_types),
               'provider': type_provider}
      except api_exceptions.HttpException as error:
        yield {'types': [],
               'provider': type_provider,
               'error': error.message}

  def Format(self, args):
    return 'yaml(provider, error, types.map().format("{0}", name))'
