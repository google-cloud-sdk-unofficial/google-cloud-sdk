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

"""Implementation of gcloud genomics datasets create.
"""

from googlecloudsdk.api_lib.genomics import genomics_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class Create(base.Command):
  """Creates a dataset with a specified name.

  A dataset is a collection of genomics objects such as reads and variants.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('--name',
                        help='The name of the dataset being created.',
                        required=True)

  @genomics_util.ReraiseHttpException
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace, All the arguments that were provided to this
        command invocation.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    Returns:
      None
    """
    apitools_client = genomics_util.GetGenomicsClient()
    genomics_messages = genomics_util.GetGenomicsMessages()

    dataset = genomics_messages.Dataset(
        name=args.name,
        projectId=genomics_util.GetProjectId(),
    )

    return apitools_client.datasets.Create(dataset)

  def Display(self, args_unused, dataset):
    """This method is called to print the result of the Run() method.

    Args:
      args_unused: The arguments that command was run with.
      dataset: The value returned from the Run() method.
    """
    log.Print('Created dataset {0}, id: {1}'.format(dataset.name, dataset.id))
