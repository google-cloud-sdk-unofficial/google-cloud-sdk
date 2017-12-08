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

"""reference sets list command."""

from googlecloudsdk.api_lib.genomics import genomics_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import list_printer
from googlecloudsdk.third_party.apitools.base.py import list_pager


class List(base.Command):
  """List genomics reference sets.

  Prints a table with summary information on reference sets.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """

    parser.add_argument('--md5checksums',
                        type=arg_parsers.ArgList(),
                        default=[],
                        help='Only return reference sets with this checksum.')

    parser.add_argument(
        '--accessions',
        type=arg_parsers.ArgList(),
        default=[],
        help='Only return reference sets from these accessions.')

    parser.add_argument(
        '--assembly-id',
        help='Only return reference sets for this assembly-id.')

    parser.add_argument(
        '--limit',
        type=int,
        help='The maximum number of results to list.')

  @genomics_util.ReraiseHttpException
  def Run(self, args):
    """Run 'referencesets list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of matching referencesets.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    genomics_util.ValidateLimitFlag(args.limit)

    apitools_client = genomics_util.GetGenomicsClient()
    req_class = (genomics_util.GetGenomicsMessages()
                 .SearchReferenceSetsRequest)
    request = req_class(
        md5checksums=args.md5checksums,
        accessions=args.accessions,
        assemblyId=args.assembly_id)
    return list_pager.YieldFromList(
        apitools_client.referencesets,
        request,
        method='Search',
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.limit,  # Use limit if any, else server default.
        field='referenceSets')

  @genomics_util.ReraiseHttpException
  def Display(self, args, result):
    """Display prints information about what just happened to stdout.

    Args:
      args: The same as the args in Run.

      result: a list of ReferenceSet objects.

    Raises:
      ValueError: if result is None or not a list
    """
    list_printer.PrintResourceList('genomics.referenceSets', result)
