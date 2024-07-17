#!/usr/bin/env python
# pylint: disable=g-unknown-interpreter
# Copyright 2012 Google Inc. All Rights Reserved.
"""Bigquery Client library for Python."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple



# To configure apiclient logging.
from absl import flags
import googleapiclient
from googleapiclient import http as http_request
from googleapiclient import model
import httplib2

import bq_utils
from clients import utils as bq_client_utils


# pylint: disable=protected-access

_ORIGINAL_GOOGLEAPI_CLIENT_RETRY_REQUEST = http_request._retry_request


# Note: All the `Optional` added here is to support tests.
def _RetryRequest(
    http: Optional[httplib2.Http],
    num_retries: int,
    req_type: Optional[str],
    sleep: Optional[Callable[[float], None]],
    rand: Optional[Callable[[int], float]],
    uri: Optional[str],
    method: Optional[str],
    *args,
    **kwargs,
):
  """Conditionally retries an HTTP request.


  If the original request fails with a specific permission error, retry it once
  without the x-goog-user-project header.

  Args:
    http: Http object to be used to execute request.
    num_retries: Maximum number of retries.
    req_type: Type of the request (used for logging retries).
    sleep: Function to sleep for random time between retries.
    rand: Function to sleep for random time between retries.
    uri: URI to be requested.
    method: HTTP method to be used.
    *args: Additional arguments passed to http.request.
    **kwargs: Additional arguments passed to http.request.

  Returns:
    resp, content - Response from the http request (may be HTTP 5xx).
  """
  # Call the original http_request._retry_request first to get the original
  # response.
  resp, content = _ORIGINAL_GOOGLEAPI_CLIENT_RETRY_REQUEST(
      http, num_retries, req_type, sleep, rand, uri, method, *args, **kwargs
  )
  if int(resp.status) == 403:
    data = json.loads(content.decode('utf-8'))
    if isinstance(data, dict) and 'message' in data['error']:
      err_message = data['error']['message']
      if 'roles/serviceusage.serviceUsageConsumer' in err_message:
        if 'headers' in kwargs and 'x-goog-user-project' in kwargs['headers']:
          del kwargs['headers']['x-goog-user-project']
          logging.info(
              'Retrying request without the x-goog-user-project header'
          )
          resp, content = _ORIGINAL_GOOGLEAPI_CLIENT_RETRY_REQUEST(
              http,
              num_retries,
              req_type,
              sleep,
              rand,
              uri,
              method,
              *args,
              **kwargs,
          )
  return resp, content


http_request._retry_request = _RetryRequest
# pylint: enable=protected-access


class BigqueryModel(model.JsonModel):
  """Adds optional global parameters to all requests."""

  def __init__(
      self,
      trace: Optional[str] = None,
      quota_project_id: Optional[str] = None,
      **kwds,
  ):
    super().__init__(**kwds)
    self.trace = trace
    self.quota_project_id = quota_project_id

  # pylint: disable=g-bad-name
  def request(
      self,
      headers: Dict[str, str],
      path_params: Dict[str, str],
      query_params: Dict[str, Any],  # TODO(b/314756043): This seems incorrect.
      body_value: object,
  ) -> Tuple[Dict[str, str], Dict[str, str], str, str]:
    """Updates outgoing request.


    Args:
      headers: dict, request headers
      path_params: dict, parameters that appear in the request path
      query_params: dict, parameters that appear in the query
      body_value: object, the request body as a Python object, which must be
        serializable.

    Returns:
      A tuple of (headers, path_params, query, body)

      headers: dict, request headers
      path_params: dict, parameters that appear in the request path
      query: string, query part of the request URI
      body: string, the body serialized in the desired wire format.
    """
    if 'trace' not in query_params and self.trace:
      headers['cookie'] = self.trace

    if self.quota_project_id:
      headers['x-goog-user-project'] = self.quota_project_id

    return super().request(headers, path_params, query_params, body_value)

  # pylint: enable=g-bad-name

  # pylint: disable=g-bad-name
  def response(self, resp: httplib2.Response, content: str) -> object:
    """Convert the response wire format into a Python object.


    Args:
      resp: httplib2.Response, the HTTP response headers and status
      content: string, the body of the HTTP response

    Returns:
      The body de-serialized as a Python object.

    Raises:
      googleapiclient.errors.HttpError if a non 2xx response is received.
    """
    logging.info('Response from server with status code: %s', resp['status'])
    return super().response(resp, content)

  # pylint: enable=g-bad-name


class BigqueryHttp(http_request.HttpRequest):
  """Converts errors into Bigquery errors."""

  def __init__(
      self,
      bigquery_model: BigqueryModel,
      *args,
      **kwds,
  ):
    super().__init__(*args, **kwds)
    logging.info(
        'URL being requested from BQ client: %s %s', kwds['method'], args[2]
    )
    self._model = bigquery_model

  @staticmethod
  def Factory(
      bigquery_model: BigqueryModel,
      use_google_auth: bool,
  ) -> Callable[..., 'BigqueryHttp']:
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
          **kwds,
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
