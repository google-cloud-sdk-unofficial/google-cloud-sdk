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

"""variantsets list command."""

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.genomics import genomics_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions


class List(base.ListCommand):
  """List Genomics variant sets in a dataset.

  Prints a table with summary information on variant sets in the dataset.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'dataset_id',
        help="""Restrict the query to variant sets within the given dataset.""")

  def Collection(self):
    return 'genomics.variantsets'

  @genomics_util.ReraiseHttpException
  def Run(self, args):
    """Run 'variantsets list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Yields:
      The list of variant sets for this dataset.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    apitools_client = genomics_util.GetGenomicsClient()
    req_class = genomics_util.GetGenomicsMessages().SearchVariantSetsRequest
    request = req_class(datasetIds=[args.dataset_id])
    try:
      for resource in list_pager.YieldFromList(
          apitools_client.variantsets,
          request,
          method='Search',
          limit=args.limit,
          batch_size_attribute='pageSize',
          batch_size=args.limit,  # Use limit if any, else server default.
          field='variantSets'):
        yield resource
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(genomics_util.GetErrorMessage(error))
