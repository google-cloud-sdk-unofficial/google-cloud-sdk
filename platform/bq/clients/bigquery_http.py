#!/usr/bin/env python
# pylint: disable=g-unknown-interpreter
# Copyright 2012 Google Inc. All Rights Reserved.
"""Bigquery Client library for Python."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
from typing import Optional


# To configure apiclient logging.
from absl import flags
import googleapiclient
from googleapiclient import http as http_request
from googleapiclient import model
import httplib2

import bq_utils
from clients import utils as bq_client_utils



class BigqueryModel(model.JsonModel):
  """Adds optional global parameters to all requests."""

  def __init__(
      self,
      trace=None,
      quota_project_id: Optional[str] = None,
      **kwds):
    super().__init__(**kwds)
    self.trace = trace
    self.quota_project_id = quota_project_id

  # pylint: disable=g-bad-name
  def request(self, headers, path_params, query_params, body_value):
    """Updates outgoing request."""
    if 'trace' not in query_params and self.trace:
      headers['cookie'] = self.trace

    if self.quota_project_id:
      headers['x-goog-user-project'] = self.quota_project_id

    return super().request(headers, path_params, query_params, body_value)

  # pylint: enable=g-bad-name

  # pylint: disable=g-bad-name
  def response(self, resp, content):
    """Convert the response wire format into a Python object."""
    logging.info('Response from server with status code: %s', resp['status'])
    return super().response(resp, content)

  # pylint: enable=g-bad-name


class BigqueryHttp(http_request.HttpRequest):
  """Converts errors into Bigquery errors."""

  def __init__(
      self,
      bigquery_model: BigqueryModel,
      *args,
      **kwds
  ):
    super().__init__(*args, **kwds)
    logging.info('URL being requested from BQ client: %s %s', kwds['method'],
                 args[2])
    self._model = bigquery_model

  @staticmethod
  def Factory(
      bigquery_model: BigqueryModel,
      use_google_auth: bool,
  ):
    """Returns a function that creates a BigqueryHttp with the given model."""

    def _Construct(*args, **kwds):
      if use_google_auth:
        user_agent = bq_utils.GetUserAgent()
        if 'headers' not in kwds:
          kwds['headers'] = {}
        elif (
            'User-Agent' in kwds['headers']
            and user_agent not in kwds['headers']['User-Agent']
        ):
          user_agent = ' '.join([user_agent, kwds['headers']['User-Agent']])
        kwds['headers']['User-Agent'] = user_agent

      captured_model = bigquery_model
      return BigqueryHttp(
          captured_model,
          *args,
          **kwds
      )

    return _Construct

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def RaiseErrorFromHttpError(e):
    """Raises a BigQueryError given an HttpError."""
    return bq_client_utils.RaiseErrorFromHttpError(e)

  # TODO(b/324243535): Delete these once the migration is complete.
  @staticmethod
  def RaiseErrorFromNonHttpError(e):
    """Raises a BigQueryError given a non-HttpError."""
    return bq_client_utils.RaiseErrorFromNonHttpError(e)

  # TODO(b/324243535): Remove pylint guards.
  # pylint: disable=g-bad-name
  def execute(self, **kwds):  # pytype: disable=signature-mismatch  # overriding-parameter-count-checks
    # pylint: enable=g-bad-name

      try:
        return super().execute(**kwds)
      except googleapiclient.errors.HttpError as e:
        # TODO(user): Remove this when apiclient supports logging
        # of error responses.
        self._model._log_response(e.resp, e.content)  # pylint: disable=protected-access
        bq_client_utils.RaiseErrorFromHttpError(e)
      except (httplib2.HttpLib2Error, IOError) as e:
        bq_client_utils.RaiseErrorFromNonHttpError(e)
