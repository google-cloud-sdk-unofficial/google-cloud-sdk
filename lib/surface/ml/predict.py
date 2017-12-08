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

from googlecloudsdk.api_lib.ml import predict
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import predict_utilities


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
    group = parser.add_mutually_exclusive_group(required=True)
    json_flag = group.add_argument(
        '--json-instances',
        help='Path to a local file from which instances are read. '
        'Instances are in JSON format; newline delimited.')
    text_flag = group.add_argument(
        '--text-instances',
        help='Path to a local file from which instances are read. '
        'Instances are in UTF-8 encoded text format; newline delimited.')
    json_flag.detailed_help = """
        Path to a local file from which instances are read.
        Instances are in JSON format; newline delimited.

        An example of the JSON instances file:

            {"images": [0.0, ..., 0.1], "key": 3}
            {"images": [0.0, ..., 0.1], "key": 2}
            ...
        """
    text_flag.detailed_help = """
        Path to a local file from which instances are read.
        Instances are in UTF-8 encoded text format; newline delimited.

        An example of the text instances file:

            107,4.9,2.5,4.5,1.7
            100,5.7,2.8,4.1,1.3
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

    # Get the input instances.
    data_format = ''
    input_file = ''
    if args.json_instances:
      data_format = 'json'
      input_file = args.json_instances
    elif args.text_instances:
      data_format = 'text'
      input_file = args.text_instances
    instances = predict_utilities.ReadInstances(input_file, data_format)

    return predict.Predict(
        model_name=args.model, version_name=args.version, instances=instances)
