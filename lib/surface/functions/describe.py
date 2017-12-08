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

"""'functions describe' command."""

from googlecloudsdk.api_lib.functions import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class Describe(base.DescribeCommand):
  """Show description of a function."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'name', help='The name of the function to describe.',
        type=util.ValidateFunctionNameOrRaise)

  @util.CatchHTTPErrorRaiseHTTPException
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter.
    """
    client = self.context['functions_client']
    messages = self.context['functions_messages']
    project = properties.VALUES.core.project.Get(required=True)
    registry = self.context['registry']
    function_ref = registry.Parse(
        args.name, params={'projectsId': project, 'locationsId': args.region},
        collection='cloudfunctions.projects.locations.functions')

    # TODO(user): Use resources.py here after b/21908671 is fixed.
    return client.projects_locations_functions.Get(
        messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=function_ref.RelativeName()))
