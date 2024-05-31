# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""recommender API recommendations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.api_lib.recommender import locations
from googlecloudsdk.api_lib.recommender import recommendation
from googlecloudsdk.api_lib.recommender import recommenders
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.recommender import flags


DETAILED_HELP = {
    'EXAMPLES':
        """
          Lists recommendations for a Cloud project.
            $ {command} --project=project-id --location=global --recommender=google.compute.instance.MachineTypeRecommender
        """,
}

DISPLAY_FORMAT = """
        table(
          name.basename(): label=RECOMMENDATION_ID,
          primaryImpact.category: label=PRIMARY_IMPACT_CATEGORY,
          stateInfo.state: label=RECOMMENDATION_STATE,
          lastRefreshTime: label=LAST_REFRESH_TIME,
          priority: label=PRIORITY,
          recommenderSubtype: label=RECOMMENDER_SUBTYPE,
          description: label=DESCRIPTION
        )
    """


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  r"""List recommendations for Google Cloud resources.

  This command lists all recommendations for the specified Google Cloud
  resource, location, and recommender. If a recommender or location is not
  specified, recommendations for all supported recommenders or locations,
  respectively, are listed. If the `--recursive` flag is set,
  recommendations for child resources and projects are also listed.
  Supported recommenders can be found here:
  https://cloud.google.com/recommender/docs/recommenders.
  The following Google Cloud resources are supported: project,
  billing_account, folder and organization.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
    """
    flags.AddParentFlagsToParser(parser)
    parser.add_argument(
        '--location',
        metavar='LOCATION',
        required=False,
        help=(
            'Location to list recommendations for. If no location is specified,'
            ' recommendations for all supported locations are listed.'
        ),
    )
    parser.add_argument(
        '--recommender',
        metavar='RECOMMENDER',
        required=False,
        help=(
            'Recommender to list recommendations for. If no recommender is'
            ' specified, recommendations for all supported recommenders are'
            ' listed. Supported recommenders can be found here:'
            ' https://cloud.google.com/recommender/docs/recommenders'
        ),
    )
    parser.add_argument(
        '--recursive',
        required=False,
        metavar='BOOLEAN_VALUE',
        type=arg_parsers.ArgBoolean(),
        default=False,
        help=("""
            By default, `--recursive` is set to false and can be ommitted.
            If `--recursive=true` is used, in addition to listing the
            recommendations for the specified
            organization, billing account, or folder, recursively list all of
            the recommendations for that resource's child resources, including
            their descendents (for example, a folder's sub-folders), and for
            that resource's child projects. For example, when using the
            `--recursive` flag and specifying an organization, the response
            lists all of the recommendations associated with that
            organization, all of the recommendations associated with that
            organization's folders and sub-folders, and all of the
            recommendations associated with that organization's child
            projects.
            """),
    )
    parser.display_info.AddFormat(DISPLAY_FORMAT)

  def Run(self, args):
    """Run 'gcloud recommender recommendations list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The list of recommendations for this project.
    """

    # Collect Assets and Locations
    if args.recursive:
      client = client_util.AssetSearchClient(client_util.DEFAULT_API_VERSION)
      args.read_mask = '*'
      args.asset_types = ['*']
      args.order_by = 'createTime'
      args.query = '*'

      if args.project:
        args.scope = 'project/' + args.project
      if args.organization:
        args.scope = 'organization/' + args.organization
      if args.organization:
        args.scope = 'folder/' + args.folder

      resources = client.SearchAllResources(args)
      locations_local = []
      for r in resources:
        # gcloud-disable-gdu-domain
        if r.assetType == 'cloudresourcemanager.googleapis.com/Project':
          if isinstance(r.project, list):
            asset = r.project[0]
          else:
            asset = r.project
          locations_local.append(f'{asset}/locations/{r.location}')
        # gcloud-disable-gdu-domain
        if r.assetType == 'cloudresourcemanager.googleapis.com/Folder':
          if isinstance(r.folder, list):
            asset = r.folder[0]
          else:
            asset = r.folder
          locations_local.append(f'{asset}/locations/{r.location}')
        # gcloud-disable-gdu-domain
        if r.assetType == 'cloudresourcemanager.googleapis.com/Organization':
          if isinstance(r.organization, list):
            asset = r.organization[0]
          else:
            asset = r.organization
          locations_local.append(f'{asset}/locations/{r.location}')
    else:
      if args.location is not None:
        locations_local = [
            flags.GetResourceSegment(args) + f'/locations/{args.location}'
        ]
      else:
        loc_client = locations.CreateClient(self.ReleaseTrack())
        locations_local = [
            loc.name
            for loc in loc_client.List(
                args.page_size,
                project=args.project,
                organization=args.organization,
                folder=args.folder,
                billing_account=args.billing_account,
            )
        ]

    # collect recommendations for all recommenders
    recommendations = []
    parent_names = []
    for location in locations_local:
      if args.recommender is not None:
        parent_names.append(f'{location}/recommenders/{args.recommender}')
      else:
        recommenders_client = recommenders.CreateClient(self.ReleaseTrack())
        recommenders_response = recommenders_client.List(args.page_size)
        parent_names.extend([
            f'{location}/recommenders/{response.name}'
            for response in recommenders_response
        ])

    recommendations_client = recommendation.CreateClient(self.ReleaseTrack())
    for parent_name in parent_names:
      new_recommendations = recommendations_client.List(
          parent_name, args.page_size
      )
      try:  # skip recommenders that the user does not have access to.
        peek = next(new_recommendations)  # execute first element of generator
      except (
          apitools_exceptions.HttpBadRequestError,
          apitools_exceptions.BadStatusCodeError,
          StopIteration,
      ):
        continue
      recommendations = itertools.chain(
          recommendations, (peek,), new_recommendations
      )

    return recommendations


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListOriginal2(base.ListCommand):
  r"""List operations for a recommendation.

  This command lists all recommendations for a given Google Cloud entity ID,
  location, and recommender. If recommender or location is not specified,
  recommendations for all supported recommenders and locations are listed.
  Supported recommenders can be found here:
  https://cloud.google.com/recommender/docs/recommenders.
  The following Google Cloud entity types are supported: project,
  billing_account, folder and organization.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
    """
    flags.AddParentFlagsToParser(parser)
    parser.add_argument(
        '--location',
        metavar='LOCATION',
        required=False,
        help=(
            'Location to list recommendations for. If no location is specified,'
            ' recommendations for all supported locations are listed.'
        ),
    )
    parser.add_argument(
        '--recommender',
        metavar='RECOMMENDER',
        required=False,
        help=(
            'Recommender to list recommendations for. If no recommender is'
            ' specified, recommendations for all supported recommenders are'
            ' listed. Supported recommenders can be found here:'
            ' https://cloud.google.com/recommender/docs/recommenders'
        ),
    )
    parser.display_info.AddFormat(DISPLAY_FORMAT)

  def Run(self, args):
    """Run 'gcloud recommender recommendations list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The list of recommendations for this project.
    """

    recommendations = []

    if args.location is not None:
      locations_local = [flags.GetResourceSegment(args) +
                         f'/locations/{args.location}']
    else:
      loc_client = locations.CreateClient(self.ReleaseTrack())
      locations_local = [
          loc.name
          for loc in loc_client.List(
              args.page_size,
              project=args.project,
              organization=args.organization,
              folder=args.folder,
              billing_account=args.billing_account,
          )
      ]

    parent_names = []
    for location in locations_local:
      if args.recommender is not None:
        parent_names.append(
            f'{location}/recommenders/{args.recommender}'
        )
      else:
        recommenders_client = recommenders.CreateClient(self.ReleaseTrack())
        recommenders_response = recommenders_client.List(args.page_size)
        parent_names.extend(
            [
                f'{location}/recommenders/{response.name}'
                for response in recommenders_response
            ]
        )

    recommendations_client = recommendation.CreateClient(self.ReleaseTrack())
    for parent_name in parent_names:
      new_recommendations = recommendations_client.List(
          parent_name, args.page_size
      )
      try:  # skip recommenders that the user does not have access to.
        peek = next(new_recommendations)  # execute first element of generator
      except (
          apitools_exceptions.HttpBadRequestError,
          apitools_exceptions.BadStatusCodeError,
          StopIteration,
      ):
        continue
      recommendations = itertools.chain(
          recommendations, (peek,), new_recommendations
      )

    return recommendations


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListOriginal(base.ListCommand):
  r"""List operations for a recommendation.

  This command lists all recommendations for a given Google Cloud entity ID,
  location, and recommender. Supported recommenders can be found here:
  https://cloud.google.com/recommender/docs/recommenders.
  The following Google Cloud entity types are supported: project,
  billing_account, folder and organization.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
    """
    flags.AddParentFlagsToParser(parser)
    parser.add_argument(
        '--location',
        metavar='LOCATION',
        required=True,
        help='Location to list recommendations for.',
    )
    parser.add_argument(
        '--recommender',
        metavar='RECOMMENDER',
        required=True,
        help=(
            'Recommender to list recommendations for. Supported recommenders'
            ' can be found here:'
            ' https://cloud.google.com/recommender/docs/recommenders.'
        ),
    )
    parser.display_info.AddFormat(DISPLAY_FORMAT)

  def Run(self, args):
    """Run 'gcloud recommender recommendations list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The list of recommendations for this project.
    """
    recommendations_client = recommendation.CreateClient(self.ReleaseTrack())
    parent_name = flags.GetRecommenderName(args)

    return recommendations_client.List(parent_name, args.page_size)
