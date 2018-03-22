# Copyright 2017 Google Inc. All Rights Reserved.
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
import cStringIO
import csv
import json
import apache_beam as beam
from apache_beam.io.textio import WriteToText
from apache_beam.transforms.combiners import Sample
import batch_prediction
from google.cloud.ml.dataflow.io.multifiles_source import ReadFromMultiFilesText
from google.cloud.ml.dataflow.io.multifiles_source import ReadFromMultiFilesTFRecord
from google.cloud.ml.dataflow.io.multifiles_source import ReadFromMultiFilesTFRecordGZip


def keys_to_csv(keys):
  output = cStringIO.StringIO()
  csv_writer = csv.writer(output)
  csv_writer.writerow(keys)
  return output.getvalue()


def values_to_csv(entry, keys):
  output = cStringIO.StringIO()
  csv_writer = csv.DictWriter(output, keys)
  csv_writer.writerow(entry)
  return output.getvalue()


def run(p, args, aggregator_dict):
  """Run the pipeline with the args and dataflow pipeline option."""
  # Create a PCollection for model directory.
  model_dir = p | "Create Model Directory" >> beam.Create([args.model_dir])

  input_file_format = args.input_file_format.lower()
  input_file_patterns = args.input_file_patterns

  # Setup reader.
  if input_file_format == "json":
    reader = p | "READ_TEXT_FILES" >> ReadFromMultiFilesText(
        input_file_patterns)
  elif input_file_format == "tfrecord":
    reader = p | "READ_TF_FILES" >> ReadFromMultiFilesTFRecord(
        input_file_patterns)
  elif input_file_format == "tfrecord_gzip":
    reader = p | "READ_TFGZIP_FILES" >> ReadFromMultiFilesTFRecordGZip(
        input_file_patterns)

  # Setup the whole pipeline.
  results, errors = (reader
                     | "BATCH_PREDICTION" >> batch_prediction.BatchPredict(
                         beam.pvalue.AsSingleton(model_dir),
                         tags=args.tags,
                         signature_name=args.signature_name,
                         batch_size=args.batch_size,
                         aggregator_dict=aggregator_dict,
                         user_project_id=args.user_project_id,
                         user_job_id=args.user_job_id,
                         framework=args.framework))

  output_file_format = args.output_file_format.lower()
  # Convert predictions to target format and then write to output files.
  if output_file_format == "json":
    _ = (results
         | "TO_JSON" >> beam.Map(json.dumps)
         | "WRITE_PREDICTION_RESULTS" >> WriteToText(
             args.output_result_prefix))
  elif output_file_format == "csv":
    fields = (results
              | "SAMPLE_SINGLE_ELEMENT" >> Sample.FixedSizeGlobally(1)
              | "GET_KEYS" >> beam.Map(
                  # entry could be None if no inputs were valid
                  lambda entry: entry[0].keys() if entry else []))
    _ = (fields
         | "KEYS_TO_CSV" >> beam.Map(keys_to_csv)
         | "WRITE_KEYS" >> WriteToText(
             args.output_result_prefix,
             file_name_suffix="_header.csv",
             shard_name_template=""))
    _ = (results
         | "VALUES_TO_CSV" >> beam.Map(values_to_csv,
                                       beam.pvalue.AsSingleton(fields))
         | "WRITE_PREDICTION_RESULTS" >> WriteToText(
             args.output_result_prefix,
             file_name_suffix=".csv",
             append_trailing_newlines=False))
  # Write prediction errors counts to output files.
  _ = (errors
       | "GROUP_BY_ERROR_TYPE" >> beam.combiners.Count.PerKey()
       | "WRITE_ERRORS" >> WriteToText(
           args.output_error_prefix))

  return p.run()
