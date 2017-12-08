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
import json
import sys

from googlecloudsdk.api_lib.ml import predict
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions as core_exceptions


class InvalidInstancesFileError(core_exceptions.Error):
  """Indicates that the input file was invalid in some way."""
  pass


def _ReadInstances(input_file=None, data_format=None):
  """Read the instances from input file.

  Args:
    input_file: An open file object for the input file.
    data_format: data format of the input file, 'json' or 'text'.

  Returns:
    A list of instances.

  Raises:
    InvalidInstancesFileError: if the input_file is empty, ill-formatted,
        or contains more than 100 instances.
  """
  instances = []
  line_num = 0

  for line_num, line in enumerate(input_file):
    line_content = line.rstrip('\n')
    if not line_content:
      raise InvalidInstancesFileError('Empty line is not allowed in the '
                                      'instances file.')
    if line_num > 100:
      raise InvalidInstancesFileError(
          'Online prediction can process no more than 100 '
          'instances per file. Please use batch prediction instead.')
    if data_format == 'json':
      try:
        instances.append(json.loads(line_content))
      except ValueError:
        raise InvalidInstancesFileError(
            'Input instances are not in JSON format. '
            'See "gcloud beta ml predict --help" for details.')
    elif data_format == 'text':
      instances.append(line_content)

  if not instances:
    raise InvalidInstancesFileError('No valid instance was found.')

  return instances


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
    group = parser.add_mutually_exclusive_group(required=True)
    json_flag = group.add_argument(
        '--json-instances',
        # TODO(b/31887749): make '--instances' an alias
        # for backward compatibility.
        '--instances',
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

    # Get the input file and format.
    data_format = 'json'
    input_file = ''
    if args.json_instances:
      data_format = 'json'
      input_file = args.json_instances
    elif args.text_instances:
      data_format = 'text'
      input_file = args.text_instances

    # Read the instances from input file.
    # TODO(b/31944251): change to a generic FileType like method for
    # reading from input files.
    instances = []
    if input_file == '-':
      instances = _ReadInstances(sys.stdin, data_format)
    else:
      with open(input_file, 'r') as f:
        instances = _ReadInstances(f, data_format)

    return predict.Predict(
        model_name=args.model, version_name=args.version, instances=instances)
