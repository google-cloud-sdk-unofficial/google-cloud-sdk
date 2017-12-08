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

"""gcloud dns project-info describe command."""

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """View Cloud DNS related information for a project.

  This command displays Cloud DNS related information for your project including
  quotas for various resources and operations.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To display Cloud DNS related information for your project, run:

            $ {command} my_project_id
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'dns_project', metavar='PROJECT_ID',
        help='The identifier for the project you want DNS related info for.')

  @util.HandleHttpError
  def Run(self, args):
    dns = self.context['dns_client']
    resources = self.context['dns_resources']
    project_ref = resources.Parse(args.dns_project, collection='dns.projects')

    return dns.projects.Get(project_ref.Request())
