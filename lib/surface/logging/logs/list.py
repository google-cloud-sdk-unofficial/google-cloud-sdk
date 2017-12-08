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

"""'logging logs list' command."""

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.third_party.apitools.base.py import list_pager


class List(base.Command):
  """Lists your project's logs."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--limit', required=False, type=int, default=None,
        help='If greater than zero, the maximum number of results.')

  @util.HandlePagerHttpError
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The list of logs.
    """
    client = self.context['logging_client_v1beta3']
    messages = self.context['logging_messages_v1beta3']
    project = properties.VALUES.core.project.Get(required=True)

    if args.limit is not None and args.limit < 0:
      args.limit = None

    request = messages.LoggingProjectsLogsListRequest(projectsId=project)

    return list_pager.YieldFromList(
        client.projects_logs, request, field='logs', limit=args.limit,
        batch_size=None, batch_size_attribute='pageSize')

  def Display(self, unused_args, result):
    """This method is called to print the result of the Run() method.

    Args:
      unused_args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    # Custom selector to return user friendly log names.
    selector = ('ID', lambda log: util.ExtractLogId(log.name))
    console_io.PrintExtendedList(result, (selector,))


List.detailed_help = {
    'DESCRIPTION': """\
        {index}
        Only logs that contain log entries are listed.
    """,
}
