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
"""ml local predict command."""

import json
import os
import subprocess
import sys


from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import local_predict
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log


class InvalidInstancesFileError(core_exceptions.Error):
  pass


# TODO(b/33039554): This piece of code is similar to that used in
# surface.ml.predict. Refactor it out to command_lib/.
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

  for line in input_file:
    line_content = line.rstrip('\n')
    if not line_content:
      raise InvalidInstancesFileError('Empty line is not allowed in the '
                                      'instances file.')
    if data_format == 'json':
      try:
        instances.append(json.loads(line_content))
      except ValueError:
        raise InvalidInstancesFileError(
            'Input instances are not in JSON format. '
            'See "gcloud beta ml local predict --help" for details.')
    elif data_format == 'text':
      instances.append(line_content)

  if not instances:
    raise InvalidInstancesFileError('No valid instance was found.')

  return instances


class LocalPredictRuntimeError(core_exceptions.Error):
  """Indicates that some error happened within local_predict."""
  pass


class InvalidReturnValueError(core_exceptions.Error):
  """Indicates that the return value from local_predict has some error."""
  pass


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Predict(base.Command):
  """Run prediction locally."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('--model-dir', required=True, help='Path to the model.')
    group = parser.add_mutually_exclusive_group(required=True)
    json_flag = group.add_argument(
        '--json-instances',
        help='Path to a local file from which instances are read. '
        'Instances are in JSON format; newline delimited.')
    text_flag = group.add_argument(
        '--text-instances',
        help='Path to a local file from which instances are read. '
        'Instances are in UTF-8 encoded text format; newline delimited.')
    json_flag.detailed_help = '''
        Path to a local file from which instances are read.
        Instances are in JSON format; newline delimited.

        An example of the JSON instances file:

            {"images": [0.0, ..., 0.1], "key": 3}
            {"images": [0.0, ..., 0.1], "key": 2}
            ...
        '''
    text_flag.detailed_help = '''
        Path to a local file from which instances are read.
        Instances are in UTF-8 encoded text format; newline delimited.

        An example of the text instances file:

            107,4.9,2.5,4.5,1.7
            100,5.7,2.8,4.1,1.3
            ...
        '''

  def Run(self, args):
    """This is what gets called when the user runs this command."""

    if sys.version_info < (2, 7):
       # googlecloudsdk.command_lib.ml.local_predict is not supposed to run
       # with python version less than 2.7.
      raise LocalPredictRuntimeError('Local prediction can only run with '
                                     'Python 2.7 or above.')

    # Read the input instances.
    data_format = ''
    input_file = ''
    if args.json_instances:
      data_format = 'json'
      input_file = args.json_instances
    elif args.text_instances:
      data_format = 'text'
      input_file = args.text_instances
    instances = []
    if input_file == '-':
      instances = _ReadInstances(sys.stdin, data_format)
    else:
      with open(input_file, 'r') as f:
        instances = _ReadInstances(f, data_format)

    # Start local prediction in a subprocess.
    command = ['python', local_predict.__file__, '--model-dir', args.model_dir]
    env = dict(os.environ)
    proc = subprocess.Popen(command, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=env)

    # Pass the instances to the process that actually runs local prediction.
    for instance in instances:
      proc.stdin.write(json.dumps(instance))
      proc.stdin.write('\n')
    proc.stdin.flush()

    # Get the results for the local prediction.
    output, err = proc.communicate()
    if proc.returncode != 0:
      raise LocalPredictRuntimeError(err)
    if err:
      log.warn(err)
    output_content = output.rstrip('\n')
    try:
      predictions = json.loads(output_content)
    except ValueError:
      raise InvalidReturnValueError('The output for prediction is not '
                                    'in JSON format: ' + output_content)
    return predictions
