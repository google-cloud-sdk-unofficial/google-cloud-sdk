# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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

"""gRPC interceptor that reports unknown regional endpoints clearly.

Split out of core.gapic_util_internal so that api_lib.util.apis_internal can
reach it without importing gapic_util_internal, which would otherwise close the
import cycle:

  api_lib.util.apis_internal
    -> core.gapic_util_internal
    -> api_lib.util.api_enablement
    -> api_lib.services.enable_api
    -> api_lib.services.{services_util, serviceusage}
    -> api_lib.util.apis_internal

This module is a pure leaf: it depends only on grpc and core.util.regional,
neither of which reaches back into the API machinery.
"""

from googlecloudsdk.core.util import regional
import grpc


class _UnavailableRegionDnsErrorResponse(grpc.Call, grpc.Future):
  """Wrapped response that raises a user-friendly error on DNS failure."""

  def __init__(self, response, region, known_available_regions):
    self._response = response
    self._region = region
    self._known_available_regions = known_available_regions

  def initial_metadata(self):
    return self._response.initial_metadata()

  def trailing_metadata(self):
    return self._response.trailing_metadata()

  def code(self):
    return self._response.code()

  def details(self):
    return self._response.details()

  def debug_error_string(self):
    return self._response.debug_error_string()

  def cancel(self):
    return self._response.cancel()

  def cancelled(self):
    return self._response.cancelled()

  def running(self):
    return self._response.running()

  def done(self):
    return self._response.done()

  def result(self, timeout=None):
    try:
      return self._response.result(timeout=timeout)
    except grpc.RpcError as e:
      regional_error = self._GetRegionalError(e)
      if regional_error:
        # Deliberately not chained with `from e`: this class was moved here
        # verbatim from core.gapic_util_internal, and setting __cause__ would
        # change the traceback users see for an unavailable region.
        raise regional_error  # pylint: disable=raise-missing-from
      raise

  def exception(self, timeout=None):
    e = self._response.exception(timeout=timeout)
    regional_error = self._GetRegionalError(e)
    if regional_error:
      return regional_error
    return e

  def traceback(self, timeout=None):
    return self._response.traceback(timeout=timeout)

  def add_done_callback(self, fn):
    return self._response.add_done_callback(fn)

  def add_callback(self, callback):
    return self._response.add_callback(callback)

  def is_active(self):
    return self._response.is_active()

  def time_remaining(self):
    return self._response.time_remaining()

  def _GetRegionalError(self, error):
    if error and error.code() == grpc.StatusCode.UNAVAILABLE:
      return regional.UnavailableRegionError(
          '{}\n\nNote: the region [{}] may not be available for this service. '
          'Known available regions are: [{}].'.format(
              error.details(),
              self._region,
              ', '.join(sorted(self._known_available_regions)),
          )
      )
    return None


class UnavailableRegionDnsErrorInterceptor(
    grpc.UnaryUnaryClientInterceptor, grpc.StreamUnaryClientInterceptor
):
  """Interceptor that catches DNS errors for invalid regions."""

  def __init__(self, region, known_available_regions):
    self._region = region
    self._known_available_regions = known_available_regions

  def intercept_call(self, continuation, client_call_details, request):
    response = continuation(client_call_details, request)
    return _UnavailableRegionDnsErrorResponse(
        response, self._region, self._known_available_regions
    )

  def intercept_unary_unary(self, continuation, client_call_details, request):
    """Intercepts a unary-unary invocation asynchronously."""
    return self.intercept_call(continuation, client_call_details, request)

  def intercept_stream_unary(
      self, continuation, client_call_details, request_iterator
  ):
    """Intercepts a stream-unary invocation asynchronously."""
    return self.intercept_call(
        continuation, client_call_details, request_iterator
    )
