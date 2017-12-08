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
"""ml jobs submit batch prediction command."""

from googlecloudsdk.api_lib.ml import jobs
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


_TF_RECORD_URL = ('https://www.tensorflow.org/versions/r0.12/how_tos/'
                  'reading_data/index.html#file-formats')


class Prediction(base.Command):
  """Start a Cloud ML batch prediction job."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    # TODO(user): move all flags definition to api_lib/ml/flags.py.
    parser.add_argument('job', help='Name of the batch prediction job.')
    parser.add_argument('--model', required=True, help='Name of the model.')
    version = parser.add_argument(
        '--version',
        help='Model version to be used.')
    version.detailed_help = """\
Model version to be used.

If unspecified, the default version of the model will be used. To list model
versions run

  $ gcloud beta ml versions list
"""
    # input location is a repeated field.
    input_paths = parser.add_argument(
        '--input-paths',
        type=arg_parsers.ArgList(min_length=1),
        required=True,
        help='Google Cloud Storage paths for instances to run prediction on.')
    input_paths.detailed_help = """\
Google Cloud Storage paths to the instances to run prediction on.

Wildcards (```*```) accepted at the *end* of a path. More than one path can be
specified if multiple file patterns are needed. For example,

    gs://my-bucket/instances*,gs://my-bucket/other-instances1

will match any objects whose names start with `instances` in `my-bucket` as well
as the `other-instances1` bucket, while

    gs://my-bucket/instance-dir/*

will match any objects in the `instance-dir` "directory" (since directories
aren't a first-class Cloud Storage concept) of `my-bucket`.
"""
    parser.add_argument(
        '--data-format',
        required=True,
        choices={
            'TEXT': ('Text files with instances separated by the new-line '
                     'character.'),
            'TF_RECORD': 'TFRecord files; see {}'.format(_TF_RECORD_URL),
            'TF_RECORD_GZIP': 'GZIP-compressed TFRecord files.'
        },
        help='Data format of the input files.')
    parser.add_argument(
        '--output-path', required=True,
        help='Google Cloud Storage path to which to save the output. '
        'Example: gs://my-bucket/output.')
    parser.add_argument(
        '--region',
        required=True,
        help='The Google Compute Engine region to run the job in.')
    flags.RUNTIME_VERSION.AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    project_ref = resources.REGISTRY.Parse(
        properties.VALUES.core.project.Get(required=True),
        collection='ml.projects')
    job = jobs.BuildBatchPredictionJob(
        job_name=args.job,
        model_name=args.model,
        version_name=args.version,
        input_paths=args.input_paths,
        data_format=args.data_format,
        output_path=args.output_path,
        region=args.region,
        runtime_version=args.runtime_version)
    return jobs.JobsClient().Create(project_ref, job)
