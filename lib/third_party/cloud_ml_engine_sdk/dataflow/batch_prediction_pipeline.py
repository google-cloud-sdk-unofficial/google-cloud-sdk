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
"""Dataflow pipeline for batch prediction in Cloud ML."""
import json
import os

import apache_beam as beam
from apache_beam.io.textio import ReadFromText
from apache_beam.io.textio import WriteToText
import batch_prediction
from google.cloud.ml.dataflow.io.tfrecordio import ReadFromTFRecord

try:
  # TODO(user): Remove this after updating to latest Beam.
  from apache_beam.io.filesystem import CompressionTypes  # pylint: disable=g-import-not-at-top
except ImportError:
  from apache_beam.io.fileio import CompressionTypes  # pylint: disable=g-import-not-at-top

FILE_LIST_SEPARATOR = ","

OUTPUT_RESULTS_FILES_BASENAME_ = "prediction.results"

OUTPUT_ERRORS_FILES_BASENAME_ = "prediction.errors_stats"


def run(p, args, aggregator_dict, cloud_logger=None):
  """Run the pipeline with the args and dataflow pipeline option."""
  # Create a PCollection for model directory.
  model_dir = p | "Create Model Directory" >> beam.Create([args.model_dir])

  input_file_format = args.input_file_format.lower()

  # Create one pcollection per input file or file pattern. And then flatten
  # them into one pcollection. The duplicated names need to be removed as the
  # file name is used to create unique labels for the PTransform.
  readers = []
  for pattern in list(set(args.input_file_patterns.split(FILE_LIST_SEPARATOR))):
    # Setup reader.
    #
    # TODO(user): Perhaps simplify the batch prediction code by using
    # CompressionTypes.AUTO.
    if input_file_format.startswith("tfrecord"):
      if input_file_format == "tfrecord_gzip":
        compression_type = CompressionTypes.GZIP
      else:
        assert input_file_format == "tfrecord"
        compression_type = CompressionTypes.UNCOMPRESSED
      reader = "READ_TFRECORD_FILES_%s" % pattern >> ReadFromTFRecord(
          pattern,
          compression_type=compression_type)

    else:
      assert input_file_format == "text"
      reader = "READ_TEXT_FILES_%s" % pattern >> ReadFromText(pattern)

    # Put the pcollections into a list and flatten later.
    readers.append(p | reader)

  # Setup the whole pipeline.
  results, errors = (readers
                     | beam.Flatten()
                     | "BATCH_PREDICTION" >> batch_prediction.BatchPredict(
                         beam.pvalue.AsSingleton(model_dir),
                         batch_size=args.batch_size,
                         aggregator_dict=aggregator_dict,
                         cloud_logger=cloud_logger))

  # Convert predictions to JSON and then write to output files.
  _ = (results
       | "TO_JSON" >> beam.Map(json.dumps)
       | "WRITE_PREDICTION_RESULTS" >> WriteToText(
           os.path.join(args.output_location, OUTPUT_RESULTS_FILES_BASENAME_)))
  # Write prediction errors counts to output files.
  _ = (errors
       | "GROUP_BY_ERROR_TYPE" >> beam.combiners.Count.PerKey()
       | "WRITE_ERRORS" >> WriteToText(
           os.path.join(args.output_location, OUTPUT_ERRORS_FILES_BASENAME_)))

  return p.run()
