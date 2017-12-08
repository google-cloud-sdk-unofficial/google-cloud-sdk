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
"""ml predict command."""
import cStringIO

from googlecloudsdk.api_lib.ml import predict
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Predict(base.Command):
  """Run Cloud ML online prediction."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('--model', required=True, help='Name of the model.')
    parser.add_argument(
        '--version',
        help='Name of the version. If unspecified, the default version '
        'of the model will be used.')
    instances_flag = parser.add_argument(
        '--instances',
        required=True,
        type=arg_parsers.BufferedFileInput(),
        help='Path to a local file from which instances are read. '
        'Instances are in text format; newline delimited.')
    instances_flag.detailed_help = """
        Path to a local file from which instances are read.
        Instances are in text format; newline delimited.

        An example of the instances file:

            {"images": [0.0, ..., 0.1], "key": 3}
            {"images": [0.0, ..., 0.1], "key": 2}
            ...
        """

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    return predict.Predict(
        model_name=args.model,
        version_name=args.version,
        input_file=cStringIO.StringIO(args.instances))
