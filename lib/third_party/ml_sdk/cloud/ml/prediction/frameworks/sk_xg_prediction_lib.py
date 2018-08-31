# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Utilities for running predictions for sklearn and xgboost frameworks.
"""
import logging
import os
import pickle
import sys

from .. import custom_code_utils
from .. import prediction_utils
from .._interfaces import PredictionClient
import numpy as np
from ..prediction_utils import PredictionError

# --------------------------
# prediction.frameworks.sk_xg_prediction_lib
# --------------------------

# Scikit-learn and XGBoost related constants
MODEL_FILE_NAME_JOBLIB = "model.joblib"
MODEL_FILE_NAME_PICKLE = "model.pkl"
MODEL_FILE_NAME_BST = "model.bst"


# This class is specific to Scikit-learn, and should be moved to a separate
# module. However due to gcloud's complicated copying mechanism we need to keep
# things in one file for now.
class SklearnClient(PredictionClient):
  """A loaded scikit-learn model to be used for prediction."""

  def __init__(self, predictor):
    self._predictor = predictor

  def predict(self, inputs, stats=None, **kwargs):
    stats = stats or prediction_utils.Stats()
    stats[prediction_utils.
          FRAMEWORK] = prediction_utils.SCIKIT_LEARN_FRAMEWORK_NAME
    stats[
        prediction_utils.ENGINE] = prediction_utils.SCIKIT_LEARN_FRAMEWORK_NAME
    with stats.time(prediction_utils.SESSION_RUN_TIME):
      try:
        return self._predictor.predict(inputs, **kwargs)
      except Exception as e:
        logging.exception("Exception while predicting with sklearn model.")
        raise PredictionError(PredictionError.FAILED_TO_RUN_MODEL,
                              "Exception during sklearn prediction: " + str(e))


# (TODO:b/68775232) This class is specific to Xgboost, and should be moved to a
# separate module. However due to gcloud's complicated copying mechanism we need
# to keep things in one file for now.
class XgboostClient(PredictionClient):
  """A loaded xgboost model to be used for prediction."""

  def __init__(self, booster):
    self._booster = booster

  def predict(self, inputs, stats=None, **kwargs):
    stats = stats or prediction_utils.Stats()
    stats[prediction_utils.FRAMEWORK] = prediction_utils.XGBOOST_FRAMEWORK_NAME
    stats[prediction_utils.ENGINE] = prediction_utils.XGBOOST_FRAMEWORK_NAME
    # TODO(b/64574886): Move this to the top once b/64574886 is resolved.
    # Before then, it would work in production since we install xgboost in
    # the Dockerfile, but the problem is the unit test that will fail to build
    # and run since xgboost can not be added as a dependency to this target.
    import xgboost as xgb  # pylint: disable=g-import-not-at-top
    try:
      inputs_dmatrix = xgb.DMatrix(inputs)
    except Exception as e:
      logging.exception("Could not initialize DMatrix from inputs: ")
      raise PredictionError(
          PredictionError.FAILED_TO_RUN_MODEL,
          "Could not initialize DMatrix from inputs: " + str(e))
    with stats.time(prediction_utils.SESSION_RUN_TIME):
      try:
        return self._booster.predict(inputs_dmatrix, **kwargs)
      except Exception as e:
        logging.exception("Exception during predicting with xgboost model: ")
        raise PredictionError(PredictionError.FAILED_TO_RUN_MODEL,
                              "Exception during xgboost prediction: " + str(e))


class SklearnModel(prediction_utils.BaseModel):
  """The implementation of Scikit-learn Model.
  """

  def __init__(self, client):
    super(SklearnModel, self).__init__(client)
    self._user_processor = custom_code_utils.create_processor_class()
    if self._user_processor and hasattr(self._user_processor,
                                        custom_code_utils.PREPROCESS_KEY):
      self._preprocess = self._user_processor.preprocess
    else:
      self._preprocess = self._null_processor
    if self._user_processor and hasattr(self._user_processor,
                                        custom_code_utils.POSTPROCESS_KEY):
      self._postprocess = self._user_processor.postprocess
    else:
      self._postprocess = self._null_processor

  def predict(self, instances, stats=None, **kwargs):
    """Override the predict method to remove TF-specific args from kwargs."""
    kwargs.pop(prediction_utils.SIGNATURE_KEY, None)
    return super(SklearnModel, self).predict(instances, stats, **kwargs)

  def preprocess(self, instances, stats=None, **kwargs):
    # TODO(b/67383676) Consider changing this to a more generic type.
    return self._preprocess(np.array(instances), **kwargs)

  def postprocess(self,
                  predicted_outputs,
                  original_input=None,
                  stats=None,
                  **kwargs):
    # TODO(b/67383676) Consider changing this to a more generic type.
    post_processed = self._postprocess(predicted_outputs, **kwargs)
    if isinstance(post_processed, np.ndarray):
      return post_processed.tolist()
    if isinstance(post_processed, list):
      return post_processed
    raise PredictionError(
        PredictionError.INVALID_OUTPUTS,
        "Bad output type returned after running %s"
        "The post-processing function should return either "
        "a numpy ndarray or a list." % self._postprocess.__name__)

  def _null_processor(self, instances, **unused_kwargs):
    return instances


class XGBoostModel(SklearnModel):
  """The implementation of XGboost Model."""


def create_sklearn_client(model_path, **unused_kwargs):
  """Returns a prediction client for the corresponding sklearn model."""
  logging.info("Loading the scikit-learn model file from %s", model_path)
  sklearn_predictor = _load_joblib_or_pickle_model(model_path)
  if not sklearn_predictor:
    error_msg = "Could not find either {} or {} in {}".format(
        MODEL_FILE_NAME_JOBLIB, MODEL_FILE_NAME_PICKLE, model_path)
    logging.critical(error_msg)
    raise PredictionError(PredictionError.FAILED_TO_LOAD_MODEL, error_msg)
  # Check if the loaded python object is an sklearn model/pipeline.
  # Ex. type(sklearn_predictor).__module__ -> 'sklearn.svm.classes'
  #     type(pipeline).__module__ -> 'sklearn.pipeline'
  if "sklearn" not in type(sklearn_predictor).__module__:
    error_msg = ("Invalid model type detected: {}.{}. Please make sure the "
                 "model file is an exported sklearn model or pipeline.").format(
                     type(sklearn_predictor).__module__,
                     type(sklearn_predictor).__name__)
    logging.critical(error_msg)
    raise PredictionError(PredictionError.FAILED_TO_LOAD_MODEL, error_msg)

  return SklearnClient(sklearn_predictor)


def create_sklearn_model(model_path, unused_flags):
  """Returns a sklearn model from the given model_path."""
  return SklearnModel(create_sklearn_client(model_path))


def create_xgboost_client(model_path, **unused_kwargs):
  """Returns a prediction client for the corresponding xgboost model."""
  logging.info("Loading the xgboost model from %s", model_path)
  booster = _load_joblib_or_pickle_model(model_path) or _load_xgboost_model(
      model_path)
  if not booster:
    error_msg = "Could not find {}, {}, or {} in {}".format(
        MODEL_FILE_NAME_JOBLIB, MODEL_FILE_NAME_PICKLE, MODEL_FILE_NAME_BST,
        model_path)
    logging.critical(error_msg)
    raise PredictionError(PredictionError.FAILED_TO_LOAD_MODEL, error_msg)
  # Check if the loaded python object is an xgboost model.
  # Expect type(booster).__module__ -> 'xgboost.core'
  if "xgboost" not in type(booster).__module__:
    error_msg = ("Invalid model type detected: {}.{}. Please make sure the "
                 "model file is an exported xgboost model.").format(
                     type(booster).__module__,
                     type(booster).__name__)
    logging.critical(error_msg)
    raise PredictionError(PredictionError.FAILED_TO_LOAD_MODEL, error_msg)

  return XgboostClient(booster)


def _load_xgboost_model(model_path):
  """Loads an xgboost model from GCS or local.

  Args:
      model_path: path to the directory containing the xgboost model.bst file.
        This path can be either a local path or a GCS path.

  Returns:
    A xgboost.Booster with the model at model_path loaded.

  Raises:
    PredictionError: If there is a problem while loading the file.
  """
  # TODO(b/64574886): Move this to the top once b/64574886 is resolved. Before
  # then, it would work in production since we install xgboost in the
  # Dockerfile, but the problem is the unit test that will fail to build and run
  # since xgboost can not be added as a dependency to this target.
  import xgboost as xgb  # pylint: disable=g-import-not-at-top
  if model_path.startswith("gs://"):
    prediction_utils.copy_model_to_local(model_path,
                                         prediction_utils.LOCAL_MODEL_PATH)
    model_path = prediction_utils.LOCAL_MODEL_PATH
  model_file = os.path.join(model_path, MODEL_FILE_NAME_BST)
  if not os.path.exists(model_file):
    return None
  try:
    return xgb.Booster(model_file=model_file)
  except xgb.core.XGBoostError as e:
    error_msg = "Could not load the model: {}. {}.".format(
        os.path.join(model_path, MODEL_FILE_NAME_BST), str(e))
    logging.critical(error_msg)
    raise PredictionError(PredictionError.FAILED_TO_LOAD_MODEL, error_msg)


def create_xgboost_model(model_path, unused_flags):
  """Returns a xgboost model from the given model_path."""
  return XGBoostModel(create_xgboost_client(model_path))


def _load_joblib_or_pickle_model(model_path):
  """Loads either a .joblib or .pkl file from GCS or from local.

  Loads one of MODEL_FILE_NAME_JOBLIB or MODEL_FILE_NAME_PICKLE files if they
  exist. This is used for both sklearn and xgboost.

  Arguments:
    model_path: The path to the directory that contains the model file. This
      path can be either a local path or a GCS path.

  Raises:
    PredictionError: If there is a problem while loading the file.

  Returns:
    A loaded scikit-learn or xgboost predictor object or None if neither
    MODEL_FILE_NAME_JOBLIB nor MODEL_FILE_NAME_PICKLE files are found.
  """
  if model_path.startswith("gs://"):
    prediction_utils.copy_model_to_local(model_path,
                                         prediction_utils.LOCAL_MODEL_PATH)
    model_path = prediction_utils.LOCAL_MODEL_PATH

  try:
    model_file_name_joblib = os.path.join(model_path, MODEL_FILE_NAME_JOBLIB)
    model_file_name_pickle = os.path.join(model_path, MODEL_FILE_NAME_PICKLE)
    if os.path.exists(model_file_name_joblib):
      model_file_name = model_file_name_joblib
      try:
        # Load joblib only when needed. If we put this at the top, we need to
        # add a dependency to sklearn anywhere that prediction_lib is called.
        from sklearn.externals import joblib  # pylint: disable=g-import-not-at-top
      except Exception as e:
        error_msg = "Could not import sklearn module."
        logging.critical(error_msg)
        raise PredictionError(PredictionError.FAILED_TO_LOAD_MODEL, error_msg)

      logging.info("Loading model %s using joblib.", model_file_name)
      return joblib.load(model_file_name)

    elif os.path.exists(model_file_name_pickle):
      model_file_name = model_file_name_pickle
      logging.info("Loading model %s using pickle.", model_file_name)
      with open(model_file_name, "rb") as f:
        return pickle.loads(f.read())

    return None

  except Exception as e:
    raw_error_msg = str(e)
    if "unsupported pickle protocol" in raw_error_msg:
      error_msg = (
          "Could not load the model: {}. {}. Please make sure the model was "
          "exported using python {}. Otherwise, please specify the correct "
          "'python_version' parameter when deploying the model.").format(
              model_file_name, raw_error_msg, sys.version_info[0])
    else:
      error_msg = "Could not load the model: {}. {}.".format(
          model_file_name, raw_error_msg)
    logging.critical(error_msg)
    raise PredictionError(PredictionError.FAILED_TO_LOAD_MODEL, error_msg)
