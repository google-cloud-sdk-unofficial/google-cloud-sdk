# Copyright 2016 Google Inc. All Rights Reserved.
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
"""ml models create command."""

from googlecloudsdk.api_lib.ml import models
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import flags
from googlecloudsdk.core import log


class CreateBeta(base.CreateCommand):
  """Create a new Cloud ML model."""

  def Collection(self):
    return 'ml.models'

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.GetModelName().AddToParser(parser)
    regions = parser.add_argument(
        '--regions',
        metavar='REGION',
        type=arg_parsers.ArgList(min_length=1),
        help=('Comma separated list of Google Cloud regions where the model '
              'will be deployed.'))
    regions.detailed_help = """\
Comma separated list of Google Cloud regions where the model will be deployed.
Currently only one region per model is supported.

Will soon be required, but defaults to 'us-central1' for now.
"""
    parser.add_argument(
        '--enable-logging',
        action='store_true',
        help=('If set, enables StackDriver Logging for online prediction.'))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    regions = args.regions
    if regions is None:
      log.warn('`--regions` flag will soon be required. Please explicitly '
               'specify a region. Using [us-central1] by default.')
      regions = ['us-central1']
    return models.ModelsClient().Create(args.model, regions,
                                        args.enable_logging)
