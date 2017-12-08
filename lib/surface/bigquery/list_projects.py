# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Implementation of gcloud bigquery list_projects.
"""

from googlecloudsdk.api_lib.bigquery import bigquery
from googlecloudsdk.calliope import base
from surface import bigquery as commands


class ListProjects(base.ListCommand):
  """Lists all the user's projects for which the Big Query API is enabled."""

  @staticmethod
  def Args(parser):
    base.LIMIT_FLAG.SetDefault(parser, bigquery.DEFAULT_RESULTS_LIMIT)

  def Collection(self):
    return 'bigquery.projects'

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespeace, All the arguments that were provided to this
        command invocation.

    Returns:
      A list of ProjectsValueListEntry objects.
    """
    apitools_client = self.context[commands.APITOOLS_CLIENT_KEY]
    bigquery_messages = self.context[commands.BIGQUERY_MESSAGES_MODULE_KEY]
    request = bigquery_messages.BigqueryProjectsListRequest(
        maxResults=args.limit or -1)
    project_list = apitools_client.projects.List(request)
    return project_list.projects
