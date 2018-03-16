# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Dataflow pipeline for batch prediction in Cloud ML.

The output data is the prediction results in the format of a list of json
object. Each key of the object is the name of the tensor to fetch. The value is
the value of that tensor.

This tool expects as input a file or file pattern. Currently it supports two
kinds of inputs.
1) Input file(s) in TFRecord format. Each record contains a string that can
   be consumed by the graph.
2) Input files(s) in Text/JSON format. Each line contains either
   a) numbers, or (possibly nested) lists of numbers.
   b) a string that can be consumed by the graph.

Note that the graph can accept one or more input tensor values. The tensor
names should be logical names that are specified when constructing the graph
where the map of logical tensor names to physical tensor names are provided
by user code.

One should also specify the model location where the model in SavedModel format
are saved. The location can be on local disk (when running locally) or on GCS.

Another mandatory flag is the output location, which is a directory on local
disk or on GCS.

This program can be used to run the pipeline or to generate a Dataflow template
for later use.
"""
import logging

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from tensorflow.python.saved_model import tag_constants
from google.cloud.ml import prediction as mlprediction
from google.cloud.ml.dataflow import _aggregators as aggregators
from google.cloud.ml.dataflow import batch_prediction_pipeline

FILE_FORMAT_SUPPORTED = ["json", "tfrecord", "tfrecord_gzip"]
OUTPUT_FORMAT_SUPPORTED = ["json", "csv"]
FRAMEWORKS_SUPPORTED = [
    mlprediction.TENSORFLOW_FRAMEWORK_NAME,
    mlprediction.SCIKIT_LEARN_FRAMEWORK_NAME,
    mlprediction.XGBOOST_FRAMEWORK_NAME
]
FILE_LIST_SEPARATOR = ","


# The default values for the pipeline options we want to customize.
DEFAULT_DATFLOW_PIPELINE_OPTIONS = {"disk_size_gb": 250}


class BatchPredictionOptions(PipelineOptions):
  """Parse the command line arguments."""

  @classmethod
  def _add_argparse_args(cls, parser):
    parser.add_argument(
        "--input_file_format",
        dest="input_file_format",
        default="json",
        choices=FILE_FORMAT_SUPPORTED,
        help=("The input file format for batch prediction. "
              "Supported formats: %s" % FILE_FORMAT_SUPPORTED))

    parser.add_argument(
        "--output_file_format",
        dest="output_file_format",
        default="json",
        choices=OUTPUT_FORMAT_SUPPORTED,
        help=("The output file format for batch prediction. "
              "Supported formats: %s" % OUTPUT_FORMAT_SUPPORTED))

    # TODO(user): consider to use "action=append"-style argparse flag.
    parser.add_value_provider_argument(
        "--input_file_patterns",
        dest="input_file_patterns",
        help=("The input data files or file patterns for batch prediction. Use "
              "%s to separate multiple files/patterns" % FILE_LIST_SEPARATOR))

    parser.add_value_provider_argument(
        "--output_result_prefix",
        dest="output_result_prefix",
        help="Output path to save the prediction results.")

    parser.add_value_provider_argument(
        "--output_error_prefix",
        dest="output_error_prefix",
        help="Output path to save the prediction errors.")

    parser.add_value_provider_argument(
        "--tags",
        dest="tags",
        default=tag_constants.SERVING,
        help="List of tags for serving graph, separated by commas.")

    parser.add_value_provider_argument(
        "--signature_name",
        dest="signature_name",
        default=None,
        help="The key of the signature map for serving signature.")

    parser.add_value_provider_argument(
        "--model_dir",
        dest="model_dir",
        help=("The path to the model where the tensorflow meta graph "
              "proto and checkpoint files are saved. Normally, it is "
              "the exported directory by session_bundle library."))

    parser.add_value_provider_argument(
        "--batch_size",
        dest="batch_size",
        type=int,
        default=64,
        help=("Number of records in one batch in the input data. All items in "
              "the same batch would be fed into tf session together so only "
              "one Session.Run() is invoked for one batch. If the batch_size "
              "has been embedded in the graph, the flag must match that value. "
              "If the first dim of the input tensors is None, this means any "
              "batch size value can be used. Thereby one can specify any int "
              "value to this flag. If no batch size is specified in the graph, "
              "the flag must take value of 1. Otherwise, the program will "
              "issue an error that shapes doesn't match."))

    parser.add_value_provider_argument(
        "--user_project_id",
        dest="user_project_id",
        help=("User's CloudML project id. It is not the project id of the "
              "Dataflow job. The logs are sent to user job project in "
              "Stackdriver with job id as its label."))

    parser.add_value_provider_argument(
        "--user_job_id",
        dest="user_job_id",
        help=("User's CloudML job id. It is not the job id of the Dataflow job."
              " The logs are sent to user job project in Stackdriver with job"
              " id as its label."))

    parser.add_value_provider_argument(
        "--framework",
        dest="framework",
        default=mlprediction.TENSORFLOW_FRAMEWORK_NAME,
        help=("The framework used to train the model against. Supported "
              "frameworks: %s" % FRAMEWORKS_SUPPORTED))


if __name__ == "__main__":
  logging.getLogger().setLevel(logging.INFO)
  dataflow_pipeline_options = PipelineOptions(
      **DEFAULT_DATFLOW_PIPELINE_OPTIONS)
  logging.info("Dataflow option: %s",
               dataflow_pipeline_options.get_all_options())
  # Create the pipeline
  p = beam.Pipeline(options=dataflow_pipeline_options)
  # Create a dict of aggregators.
  aggregator_dict = aggregators.CreateAggregatorsDict()
  # Actually start the pipeline
  result = batch_prediction_pipeline.run(
      p,
      dataflow_pipeline_options.view_as(BatchPredictionOptions),
      aggregator_dict)
  # From beam 2.1.0, the main thread exits. When using DirectRunner, we want to
  # explicitly block the execution when DirectRunner is used.
  if dataflow_pipeline_options.get_all_options().get("runner",
                                                     None) != "DataflowRunner":
    result.wait_until_finish()
