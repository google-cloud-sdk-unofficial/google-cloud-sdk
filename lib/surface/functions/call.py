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

"""'functions call' command."""

from googlecloudsdk.api_lib.functions import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class Call(base.Command):
  """Call function synchronously for testing."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'name', help='Name of the function to be called.',
        type=util.ValidateFunctionNameOrRaise)
    parser.add_argument(
        '--data', default='',
        help='Data passed to the function (JSON string)')

  @util.CatchHTTPErrorRaiseHTTPException
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Function call results (error or result with execution id)
    """
    project = properties.VALUES.core.project.Get(required=True)
    # TODO(b/25364251): Use resource parser.
    name = 'projects/{0}/regions/{1}/functions/{2}'.format(
        project, args.region, args.name)
    client = self.context['functions_client']
    messages = self.context['functions_messages']
    return client.projects_regions_functions.Call(
        messages.CloudfunctionsProjectsRegionsFunctionsCallRequest(
            name=name,
            callFunctionRequest=messages.CallFunctionRequest(data=args.data)))
