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
"""Cloud ML batch prediction dataflow transforms.
"""
# TODO(user): add a unittest to test logging futures.

import datetime
import json
import logging
import threading
import traceback



import apache_beam as beam
from apache_beam.options.value_provider import StaticValueProvider
from apache_beam.options.value_provider import ValueProvider
from apache_beam.transforms import window
from apache_beam.utils.windowed_value import WindowedValue

from google.cloud.ml import prediction as mlprediction
from google.cloud.ml.dataflow import _aggregators as aggregators
from google.cloud.ml.dataflow import _cloud_logging_client as cloud_logging_client
from google.cloud.ml.dataflow import _error_filter as error_filter
from tensorflow.python.saved_model import tag_constants

DEFAULT_BATCH_SIZE = 1000  # 1K instances per batch when evaluating models.
LOG_SIZE_LIMIT = 1000  # 1K bytes for the input field in log entries.
LOG_NAME = "worker"
_METRICS_NAMESPACE = "cloud_ml_batch_predict"


class EmitAsBatchDoFn(beam.DoFn):
  """A DoFn that buffers the records and emits them batch by batch."""

  def __init__(self, desired_batch_size):
    """Constructor of EmitAsBatchDoFn beam.DoFn class.

    Args:
      desired_batch_size: the desired size we want to buffer the records before
        emitting.
    """
    # TODO(user): Remove the "if" section when the direct use of
    # EmitAsBatchDoFn() is retired from ml_transform.
    if isinstance(desired_batch_size, int):
      desired_batch_size = StaticValueProvider(int, desired_batch_size)
    self._desired_batch_size = desired_batch_size
    self._batch = []

    # Metrics.
    self._batch_size_distribution = beam.metrics.Metrics.distribution(
        _METRICS_NAMESPACE, "batch_size")
    self._num_instances = beam.metrics.Metrics.counter(_METRICS_NAMESPACE,
                                                       "num_instances")

  def _flush_batch(self):
    self._batch_size_distribution.update(len(self._batch))
    self._num_instances.inc(len(self._batch))
    result = self._batch
    self._batch = []
    return result

  # TODO(user): Remove the context and try catch after sdk update
  def process(self, element):
    try:
      element = element.element
    except AttributeError:
      pass

    self._batch.append(element)
    if len(self._batch) >= self._desired_batch_size.get():
      yield self._flush_batch()

  def finish_bundle(self, context=None):
    if self._batch:
      yield WindowedValue(self._flush_batch(), -1, [window.GlobalWindow()])


class PredictionDoFn(beam.DoFn):
  """A DoFn class loading the model to create session and performing prediction.

  The input PCollection consists of a list of strings from the input files.

  The DoFn first loads model from a given path where meta graph data and
  checkpoint data are exported to. Then if the there is only one string input
  tensor or the model needs to preprocess the input, it directly passes the
  data to prediction. Otherwise, it tries to load the data into JSON.

  Then it batches the inputs of each instance into one feed_dict. After that, it
  runs session and predicts the interesting values for all the instances.
  Finally it emits the prediction result for each individual instance.
  """

  class _ModelState(object):
    """Atomic representation of the in-memory state of the model."""

    def __init__(self,
                 model_dir,
                 tags,
                 framework=mlprediction.TENSORFLOW_FRAMEWORK_NAME):
      self.model_dir = model_dir
      client = mlprediction.create_client(framework, model_dir, tags)
      self.model = mlprediction.create_model(client, model_dir, framework)

  # TODO(b/33746781): Get rid of this and instead use self._model_state for
  # all initialization detection.
  _thread_local = threading.local()

  def __init__(self,
               aggregator_dict=None,
               user_project_id="",
               user_job_id="",
               tags=tag_constants.SERVING,
               signature_name="",
               skip_preprocessing=False,
               target="",
               config=None,
               framework=mlprediction.TENSORFLOW_FRAMEWORK_NAME):
    """Constructor of Prediction beam.DoFn class.

    Args:
      aggregator_dict: A dict of aggregators containing maps from counter name
                       to the aggregator.
      user_project_id: A string. The project to which the logs will be sent.
      user_job_id:     A string. The job to which the logs will be sent.
      tags: A comma-separated string that contains a list of tags for serving
            graph.
      signature_name: A string to map into the signature map to get the serving
                     signature.
      skip_preprocessing: bool whether to skip preprocessing even when
                          the metadata.yaml/metadata.json file exists.
      target: The execution engine to connect to. See target in tf.Session(). In
              most cases, users should not set the target.
      config: A ConfigProto proto with configuration options. See config in
              tf.Session()
      framework: The framework used to train this model. Available frameworks:
               "TENSORFLOW", "SCIKIT_LEARN", and "XGBOOST".

    Side Inputs:
      model_dir: The directory containing the model to load and the
                 checkpoint files to restore the session.
    """
    self._target = target
    self._user_project_id = user_project_id
    self._user_job_id = user_job_id
    self._tags = tags
    self._signature_name = signature_name
    self._skip_preprocessing = skip_preprocessing
    self._config = config
    self._aggregator_dict = aggregator_dict
    self._model_state = None
    self._cloud_logger = None
    self._tag_list = []
    self._framework = framework
    # Metrics.
    self._model_load_seconds_distribution = beam.metrics.Metrics.distribution(
        _METRICS_NAMESPACE, "model_load_seconds")
    self._batch_process_ms_distribution = beam.metrics.Metrics.distribution(
        _METRICS_NAMESPACE, "batch_process_milliseconds")

  def start_bundle(self):
    user_project_id = self._user_project_id.get()
    user_job_id = self._user_job_id.get()
    if user_project_id and user_job_id:
      self._cloud_logger = cloud_logging_client.MLCloudLoggingClient.create(
          user_project_id, user_job_id, LOG_NAME, "jsonPayload")
    self._tag_list = self._tags.get().split(",")
    self._signature_name = self._signature_name.get()

  def _create_snippet(self, input_data):
    """Truncate the input data to create a snippet."""
    try:
      input_snippet = "\n".join(str(x) for x in input_data)
      return unicode(input_snippet[:LOG_SIZE_LIMIT], errors="replace")
    except Exception:  # pylint: disable=broad-except
      logging.warning("Failed to create snippet from input: [%s].",
                      traceback.format_exc())
      return "Input snippet is unavailable."

  def process(self, element, model_dir):
    try:
      if isinstance(model_dir, ValueProvider):
        model_dir = model_dir.get()
      framework = self._framework.get()
      if self._model_state is None:
        if (getattr(self._thread_local, "model_state", None) is None or
            self._thread_local.model_state.model_dir != model_dir):
          start = datetime.datetime.now()
          self._thread_local.model_state = self._ModelState(
              model_dir, self._tag_list, framework)
          self._model_load_seconds_distribution.update(
              int((datetime.datetime.now() - start).total_seconds()))
        self._model_state = self._thread_local.model_state
      else:
        assert self._model_state.model_dir == model_dir

      # Measure the processing time.
      start = datetime.datetime.now()
      # Try to load it.
      if framework == mlprediction.TENSORFLOW_FRAMEWORK_NAME:
        # Even though predict() checks the signature in TensorFlowModel,
        # we need to duplicate this check here to determine the single string
        # input case.
        self._signature_name, signature = self._model_state.model.get_signature(
            self._signature_name)
        if self._model_state.model.is_single_string_input(signature):
          loaded_data = element
        else:
          loaded_data = [json.loads(d) for d in element]
      else:
        loaded_data = [json.loads(d) for d in element]
      instances = mlprediction.decode_base64(loaded_data)
      # Actual prediction occurs.
      kwargs = {}
      if self._signature_name:
        kwargs = {"signature_name": self._signature_name}
      inputs, predictions = self._model_state.model.predict(instances, **kwargs)

      predictions = list(predictions)

      if self._aggregator_dict:
        self._aggregator_dict[aggregators.AggregatorName.ML_PREDICTIONS].inc(
            len(predictions))

      # For successful processing, record the time.
      td = datetime.datetime.now() - start
      time_delta_in_ms = int(
          td.microseconds / 10**3  + (td.seconds + td.days * 24 * 3600) * 10**3)
      self._batch_process_ms_distribution.update(time_delta_in_ms)

      for i, p in zip(inputs, predictions):
        yield i, p

    except mlprediction.PredictionError as e:
      logging.error("Got a known exception: [%s]\n%s", str(e),
                    traceback.format_exc())
      clean_error_detail = error_filter.filter_tensorflow_error(e.error_detail)
      if self._cloud_logger:
        # TODO(user): consider to write a sink to buffer the logging events. It
        # also eliminates the restarting/duplicated running issue.
        self._cloud_logger.write_error_message(clean_error_detail,
                                               self._create_snippet(element))
      # Track in the counter.
      if self._aggregator_dict:
        counter_name = aggregators.AggregatorName.ML_FAILED_PREDICTIONS
        self._aggregator_dict[counter_name].inc(len(element))

      # reraise failure to load model as permanent exception to end dataflow job
      if e.error_code == mlprediction.PredictionError.FAILED_TO_LOAD_MODEL:
        raise beam.utils.retry.PermanentException(clean_error_detail)
      try:
        yield beam.pvalue.TaggedOutput("errors", (clean_error_detail,
                                                  element))
      except AttributeError:
        yield beam.pvalue.SideOutputValue("errors", (clean_error_detail,
                                                     element))

    except Exception as e:  # pylint: disable=broad-except
      logging.error("Got an unknown exception: [%s].", traceback.format_exc())
      if self._cloud_logger:
        self._cloud_logger.write_error_message(
            str(e), self._create_snippet(element))
      # Track in the counter.
      if self._aggregator_dict:
        counter_name = aggregators.AggregatorName.ML_FAILED_PREDICTIONS
        self._aggregator_dict[counter_name].inc(len(element))

      try:
        yield beam.pvalue.TaggedOutput("errors", (str(e), element))
      except AttributeError:
        yield beam.pvalue.SideOutputValue("errors", (str(e), element))


class BatchPredict(beam.PTransform):
  """A transform to load tensorflow model and do prediction.

  The transform first reads prediction instance from the input. Then it loads
  the tensorflow model from disk and restores the session. For each input, it
  performs prediction and emits the results.
  """

  def __init__(self,
               model_dir,
               tags=tag_constants.SERVING,
               signature_name="",
               batch_size=DEFAULT_BATCH_SIZE,
               aggregator_dict=None,
               user_project_id="",
               user_job_id="",
               target="",
               config=None,
               return_input=False,
               framework=mlprediction.TENSORFLOW_FRAMEWORK_NAME,
               **kwargs):
    """Constructs the transform.

    Args:
      model_dir: a Pvalue singleton of model directory that contains model
                 graph and model parameter files.
      tags: A comma-separated string that contains a list of tags for
            serving graph.
      signature_name: A string to map into the signature map to get the serving
                     signature.
      batch_size: the number of records in one batch or a ValueProvider of
                  integer.  All the instances in the same batch would be fed
                  into tf session together thereby only on Session.Run() is
                  invoked for one batch.
      aggregator_dict: A dict of aggregators containing maps from counter name
                 to the aggregator.
      user_project_id: A string or a ValueProvider of string.
                       The project to which the logs will be sent.
      user_job_id: A string or a ValueProvider of string. The job to which
                   the logs will be sent.
      target: The execution engine to connect to. Optional. See target in
              tf.Session()
      config: A ConfigProto proto with configuration options. Optional. See
              config in tf.Session()
      return_input: if true, the transforms returns a tuple of [input, output]
                    otherwise only the output is returned.
      framework: The framework used to train this model. Available frameworks:
                 "TENSORFLOW", "SCIKIT_LEARN", and "XGBOOST".
      **kwargs: Other named arguments, e.g. label, passed to base PTransform.
    """
    super(BatchPredict, self).__init__(**kwargs)

    if not isinstance(batch_size, (int, ValueProvider)):
      raise TypeError("%s: batch_size must be of type int"
                      " or ValueProvider; got %r instead"
                      % (self.__class__.__name__, batch_size))
    self._batch_size = batch_size
    if isinstance(batch_size, int):
      self._batch_size = StaticValueProvider(int, batch_size)

    self._framework = framework
    if isinstance(framework, basestring):
      self._framework = StaticValueProvider(str, framework)

    # Tags
    self._tags = tags
    if isinstance(tags, basestring):
      self._tags = StaticValueProvider(str, tags)
    # Signature name
    if not isinstance(signature_name, (basestring, ValueProvider)):
      raise TypeError("%s: signature_name must be of type string"
                      " or ValueProvider; got %r instead"
                      % (self.__class__.__name__, signature_name))
    self._signature_name = signature_name
    if isinstance(signature_name, basestring):
      self._signature_name = StaticValueProvider(str, signature_name)

    # user_project_id
    if not isinstance(user_project_id, (basestring, ValueProvider)):
      raise TypeError("%s: user_project_id must be of type string"
                      " or ValueProvider; got %r instead"
                      % (self.__class__.__name__, user_project_id))
    self._user_project_id = user_project_id
    if isinstance(user_project_id, basestring):
      self._user_project_id = StaticValueProvider(str, user_project_id)

    # user_job_id
    if not isinstance(user_job_id, (basestring, ValueProvider)):
      raise TypeError("%s: user_job_id must be of type string"
                      " or ValueProvider; got %r instead"
                      % (self.__class__.__name__, user_job_id))
    self._user_job_id = user_job_id
    if isinstance(user_job_id, basestring):
      self._user_job_id = StaticValueProvider(str, user_job_id)

    # None-value-provider variable.
    self._aggregator_dict = aggregator_dict
    self._target = target
    self._config = config
    self._model_dir = model_dir
    self._return_input = return_input

  # TODO(b/33677990): Remove apply method.
  def apply(self, data):
    return self.expand(data)

  def expand(self, data):
    """Apply the transform.

    Args:
      data: A PCollection of records containing the data to predict.

    Returns:
      A PCollection of prediction records and errors
    """
    result = (data | "Batch" >> beam.ParDo(EmitAsBatchDoFn(self._batch_size))
              | "Prediction" >> beam.ParDo(
                  PredictionDoFn(
                      self._aggregator_dict,
                      self._user_project_id,
                      self._user_job_id,
                      self._tags,
                      self._signature_name,
                      skip_preprocessing=False,
                      target=self._target,
                      config=self._config,
                      framework=self._framework), self._model_dir).with_outputs(
                          "errors", main="main"))
    input_output, errors = result.main, result.errors
    if self._return_input:
      output_data = input_output
    else:
      output_data = input_output | beam.Map(lambda (_, prediction): prediction)

    return output_data, errors
