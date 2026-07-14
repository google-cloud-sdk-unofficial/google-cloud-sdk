# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Update the developer connect git repository link."""

import datetime

from googlecloudsdk.api_lib.developer_connect.insights_configs import insights_config
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.developer_connect import flags
from googlecloudsdk.command_lib.developer_connect import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


DETAILED_HELP = {
    'DESCRIPTION': """
          Update a git repository link to enable metrics collection.
          """,
    'EXAMPLES': """
          To update a git repository link to enable metrics collection, run:

            $ {command} developer-connect connections git-repository-links update <LINK> --collect-metrics
          """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Update(base.UpdateCommand):
  """Update a git repository link to enable metrics collection."""

  @staticmethod
  def Args(parser):
    # Relevant argument.
    resource_args.AddGitRepositoryLinkResourceArg(parser, verb='update')
    flags.AddCollectMetricsArgument(parser)

  def Run(self, args):
    if not args.collect_metrics:
      log.status.Print('No updates specified.')
      return
    max_wait = datetime.timedelta(seconds=30)
    client = insights_config.InsightsConfigClient(base.ReleaseTrack.BETA)
    git_repository_link_ref = args.CONCEPTS.git_repository_link.Parse()
    project_id = git_repository_link_ref.projectsId
    location_id = git_repository_link_ref.locationsId
    repo_link_id = git_repository_link_ref.gitRepositoryLinksId
    insights_config_ref = resources.REGISTRY.Parse(
        repo_link_id + '-metrics',
        params={
            'projectsId': project_id,
            'locationsId': location_id,
            'insightsConfigsId': repo_link_id + '-metrics',
        },
        collection='developerconnect.projects.locations.insightsConfigs',
    )
    log.CreatedResource(
        'create Insights Config [{0}].'.format(insights_config_ref)
    )

    # Construct the request message
    source_config = {
        'git-repository-link': git_repository_link_ref.RelativeName()
    }
    try:
      operation = client.create(
          insight_config_ref=insights_config_ref,
          app_hub=None,
          target_projects=None,
          user_artifact_configs=None,
          source_config=source_config,
      )

    except exceptions.HttpException as e:
      log.status.Print(
          'Failed to create the insight config {}.'.format(
              insights_config_ref.RelativeName()
          )
      )
      raise e

    log.status.Print(
        'Creating the insight config {}.'.format(
            insights_config_ref.RelativeName()
        )
    )
    return client.wait_for_operation(
        operation_ref=client.get_operation_ref(operation),
        message='Waiting for operation [{}] to be completed...'.format(
            client.get_operation_ref(operation).RelativeName()
        ),
        has_result=True,
        max_wait=max_wait,
    )


Update.detailed_help = DETAILED_HELP
