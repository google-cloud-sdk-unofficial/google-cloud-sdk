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

"""'logging resource-descriptors list' command."""

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import list_printer
from googlecloudsdk.third_party.apitools.base.py import list_pager


class List(base.Command):
  """Lists all available resource descriptors."""

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
      The list of log entries.
    """
    client = self.context['logging_client_v2beta1']
    messages = self.context['logging_messages_v2beta1']

    if args.limit is not None and args.limit < 0:
      args.limit = None

    return list_pager.YieldFromList(
        client.monitoredResourceDescriptors,
        messages.LoggingMonitoredResourceDescriptorsListRequest(),
        field='resourceDescriptors', limit=args.limit, batch_size=args.limit,
        batch_size_attribute='pageSize')

  def Display(self, unused_args, result):
    """This method is called to print the result of the Run() method.

    Args:
      unused_args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    list_printer.PrintResourceList('logging.resourceDescriptors', result)


List.detailed_help = {
    'DESCRIPTION': """\
        Lists all available resource descriptors that are used by Cloud Logging.
        Each log entry must be associated with a valid resource descriptor.
    """,
}
