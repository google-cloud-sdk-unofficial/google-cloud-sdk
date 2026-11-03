# -*- coding: utf-8 -*-
# Copyright 2025 Google LLC
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
#
import logging
import json  # type: ignore

from google.auth.transport.requests import AuthorizedSession  # type: ignore
from google.auth import credentials as ga_credentials  # type: ignore
from google.api_core import exceptions as core_exceptions
from google.api_core import retry as retries
from google.api_core import rest_helpers
from google.api_core import rest_streaming
from google.api_core import gapic_v1
import cloudsdk.google.protobuf

from cloudsdk.google.protobuf import json_format

from requests import __version__ as requests_version
import dataclasses
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import warnings


from cloudsdk.google.protobuf import empty_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.logging_v2.types import logging_metrics


from .rest_base import _BaseMetricsServiceV2RestTransport
from .base import DEFAULT_CLIENT_INFO as BASE_DEFAULT_CLIENT_INFO

try:
    OptionalRetry = Union[retries.Retry, gapic_v1.method._MethodDefault, None]
except AttributeError:  # pragma: NO COVER
    OptionalRetry = Union[retries.Retry, object, None]  # type: ignore

try:
    from google.api_core import client_logging  # type: ignore
    CLIENT_LOGGING_SUPPORTED = True  # pragma: NO COVER
except ImportError:  # pragma: NO COVER
    CLIENT_LOGGING_SUPPORTED = False

_LOGGER = logging.getLogger(__name__)

DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(
    gapic_version=BASE_DEFAULT_CLIENT_INFO.gapic_version,
    grpc_version=None,
    rest_version=f"requests@{requests_version}",
)

if hasattr(DEFAULT_CLIENT_INFO, "protobuf_runtime_version"):  # pragma: NO COVER
    DEFAULT_CLIENT_INFO.protobuf_runtime_version = cloudsdk.google.protobuf.__version__


class MetricsServiceV2RestInterceptor:
    """Interceptor for MetricsServiceV2.

    Interceptors are used to manipulate requests, request metadata, and responses
    in arbitrary ways.
    Example use cases include:
    * Logging
    * Verifying requests according to service or custom semantics
    * Stripping extraneous information from responses

    These use cases and more can be enabled by injecting an
    instance of a custom subclass when constructing the MetricsServiceV2RestTransport.

    .. code-block:: python
        class MyCustomMetricsServiceV2Interceptor(MetricsServiceV2RestInterceptor):
            def pre_create_log_metric(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_create_log_metric(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_delete_log_metric(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def pre_get_log_metric(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_log_metric(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_log_metrics(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_log_metrics(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_update_log_metric(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_update_log_metric(self, response):
                logging.log(f"Received response: {response}")
                return response

        transport = MetricsServiceV2RestTransport(interceptor=MyCustomMetricsServiceV2Interceptor())
        client = MetricsServiceV2Client(transport=transport)


    """
    def pre_create_log_metric(self, request: logging_metrics.CreateLogMetricRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_metrics.CreateLogMetricRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for create_log_metric

        Override in a subclass to manipulate the request or metadata
        before they are sent to the MetricsServiceV2 server.
        """
        return request, metadata

    def post_create_log_metric(self, response: logging_metrics.LogMetric) -> logging_metrics.LogMetric:
        """Post-rpc interceptor for create_log_metric

        DEPRECATED. Please use the `post_create_log_metric_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the MetricsServiceV2 server but before
        it is returned to user code. This `post_create_log_metric` interceptor runs
        before the `post_create_log_metric_with_metadata` interceptor.
        """
        return response

    def post_create_log_metric_with_metadata(self, response: logging_metrics.LogMetric, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_metrics.LogMetric, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for create_log_metric

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the MetricsServiceV2 server but before it is returned to user code.

        We recommend only using this `post_create_log_metric_with_metadata`
        interceptor in new development instead of the `post_create_log_metric` interceptor.
        When both interceptors are used, this `post_create_log_metric_with_metadata` interceptor runs after the
        `post_create_log_metric` interceptor. The (possibly modified) response returned by
        `post_create_log_metric` will be passed to
        `post_create_log_metric_with_metadata`.
        """
        return response, metadata

    def pre_delete_log_metric(self, request: logging_metrics.DeleteLogMetricRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_metrics.DeleteLogMetricRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for delete_log_metric

        Override in a subclass to manipulate the request or metadata
        before they are sent to the MetricsServiceV2 server.
        """
        return request, metadata

    def pre_get_log_metric(self, request: logging_metrics.GetLogMetricRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_metrics.GetLogMetricRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for get_log_metric

        Override in a subclass to manipulate the request or metadata
        before they are sent to the MetricsServiceV2 server.
        """
        return request, metadata

    def post_get_log_metric(self, response: logging_metrics.LogMetric) -> logging_metrics.LogMetric:
        """Post-rpc interceptor for get_log_metric

        DEPRECATED. Please use the `post_get_log_metric_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the MetricsServiceV2 server but before
        it is returned to user code. This `post_get_log_metric` interceptor runs
        before the `post_get_log_metric_with_metadata` interceptor.
        """
        return response

    def post_get_log_metric_with_metadata(self, response: logging_metrics.LogMetric, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_metrics.LogMetric, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for get_log_metric

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the MetricsServiceV2 server but before it is returned to user code.

        We recommend only using this `post_get_log_metric_with_metadata`
        interceptor in new development instead of the `post_get_log_metric` interceptor.
        When both interceptors are used, this `post_get_log_metric_with_metadata` interceptor runs after the
        `post_get_log_metric` interceptor. The (possibly modified) response returned by
        `post_get_log_metric` will be passed to
        `post_get_log_metric_with_metadata`.
        """
        return response, metadata

    def pre_list_log_metrics(self, request: logging_metrics.ListLogMetricsRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_metrics.ListLogMetricsRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_log_metrics

        Override in a subclass to manipulate the request or metadata
        before they are sent to the MetricsServiceV2 server.
        """
        return request, metadata

    def post_list_log_metrics(self, response: logging_metrics.ListLogMetricsResponse) -> logging_metrics.ListLogMetricsResponse:
        """Post-rpc interceptor for list_log_metrics

        DEPRECATED. Please use the `post_list_log_metrics_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the MetricsServiceV2 server but before
        it is returned to user code. This `post_list_log_metrics` interceptor runs
        before the `post_list_log_metrics_with_metadata` interceptor.
        """
        return response

    def post_list_log_metrics_with_metadata(self, response: logging_metrics.ListLogMetricsResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_metrics.ListLogMetricsResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_log_metrics

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the MetricsServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_log_metrics_with_metadata`
        interceptor in new development instead of the `post_list_log_metrics` interceptor.
        When both interceptors are used, this `post_list_log_metrics_with_metadata` interceptor runs after the
        `post_list_log_metrics` interceptor. The (possibly modified) response returned by
        `post_list_log_metrics` will be passed to
        `post_list_log_metrics_with_metadata`.
        """
        return response, metadata

    def pre_update_log_metric(self, request: logging_metrics.UpdateLogMetricRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_metrics.UpdateLogMetricRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for update_log_metric

        Override in a subclass to manipulate the request or metadata
        before they are sent to the MetricsServiceV2 server.
        """
        return request, metadata

    def post_update_log_metric(self, response: logging_metrics.LogMetric) -> logging_metrics.LogMetric:
        """Post-rpc interceptor for update_log_metric

        DEPRECATED. Please use the `post_update_log_metric_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the MetricsServiceV2 server but before
        it is returned to user code. This `post_update_log_metric` interceptor runs
        before the `post_update_log_metric_with_metadata` interceptor.
        """
        return response

    def post_update_log_metric_with_metadata(self, response: logging_metrics.LogMetric, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_metrics.LogMetric, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for update_log_metric

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the MetricsServiceV2 server but before it is returned to user code.

        We recommend only using this `post_update_log_metric_with_metadata`
        interceptor in new development instead of the `post_update_log_metric` interceptor.
        When both interceptors are used, this `post_update_log_metric_with_metadata` interceptor runs after the
        `post_update_log_metric` interceptor. The (possibly modified) response returned by
        `post_update_log_metric` will be passed to
        `post_update_log_metric_with_metadata`.
        """
        return response, metadata


@dataclasses.dataclass
class MetricsServiceV2RestStub:
    _session: AuthorizedSession
    _host: str
    _interceptor: MetricsServiceV2RestInterceptor


class MetricsServiceV2RestTransport(_BaseMetricsServiceV2RestTransport):
    """REST backend synchronous transport for MetricsServiceV2.

    Service for configuring logs-based metrics.

    This class defines the same methods as the primary client, so the
    primary client can load the underlying transport implementation
    and call it.

    It sends JSON representations of protocol buffers over HTTP/1.1
    """

    def __init__(self, *,
            host: str = 'logging.googleapis.com',
            credentials: Optional[ga_credentials.Credentials] = None,
            credentials_file: Optional[str] = None,
            scopes: Optional[Sequence[str]] = None,
            client_cert_source_for_mtls: Optional[Callable[[
                ], Tuple[bytes, bytes]]] = None,
            quota_project_id: Optional[str] = None,
            client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
            always_use_jwt_access: Optional[bool] = False,
            url_scheme: str = 'https',
            interceptor: Optional[MetricsServiceV2RestInterceptor] = None,
            api_audience: Optional[str] = None,
            ) -> None:
        """Instantiate the transport.

       NOTE: This REST transport functionality is currently in a beta
       state (preview). We welcome your feedback via a GitHub issue in
       this library's repository. Thank you!

        Args:
            host (Optional[str]):
                 The hostname to connect to (default: 'logging.googleapis.com').
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.

            credentials_file (Optional[str]): Deprecated. A file with credentials that can
                be loaded with :func:`google.auth.load_credentials_from_file`.
                This argument is ignored if ``channel`` is provided. This argument will be
                removed in the next major version of this library.
            scopes (Optional(Sequence[str])): A list of scopes. This argument is
                ignored if ``channel`` is provided.
            client_cert_source_for_mtls (Callable[[], Tuple[bytes, bytes]]): Client
                certificate to configure mutual TLS HTTP channel. It is ignored
                if ``channel`` is provided.
            quota_project_id (Optional[str]): An optional project to use for billing
                and quota.
            client_info (google.api_core.gapic_v1.client_info.ClientInfo):
                The client info used to send a user-agent string along with
                API requests. If ``None``, then default info will be used.
                Generally, you only need to set this if you are developing
                your own client library.
            always_use_jwt_access (Optional[bool]): Whether self signed JWT should
                be used for service account credentials.
            url_scheme: the protocol scheme for the API endpoint.  Normally
                "https", but for testing or local servers,
                "http" can be specified.
        """
        # Run the base constructor
        # TODO(yon-mg): resolve other ctor params i.e. scopes, quota, etc.
        # TODO: When custom host (api_endpoint) is set, `scopes` must *also* be set on the
        # credentials object
        super().__init__(
            host=host,
            credentials=credentials,
            client_info=client_info,
            always_use_jwt_access=always_use_jwt_access,
            url_scheme=url_scheme,
            api_audience=api_audience
        )
        self._session = AuthorizedSession(
            self._credentials, default_host=self.DEFAULT_HOST)
        if client_cert_source_for_mtls:
            self._session.configure_mtls_channel(client_cert_source_for_mtls)
        self._interceptor = interceptor or MetricsServiceV2RestInterceptor()
        self._prep_wrapped_messages(client_info)

    class _CreateLogMetric(_BaseMetricsServiceV2RestTransport._BaseCreateLogMetric, MetricsServiceV2RestStub):
        def __hash__(self):
            return hash("MetricsServiceV2RestTransport.CreateLogMetric")

        @staticmethod
        def _get_response(
            host,
            metadata,
            query_params,
            session,
            timeout,
            transcoded_request,
            body=None):

            uri = transcoded_request['uri']
            method = transcoded_request['method']
            headers = dict(metadata)
            headers['Content-Type'] = 'application/json'
            response = getattr(session, method)(
                "{host}{uri}".format(host=host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
                data=body,
                )
            return response

        def __call__(self,
                request: logging_metrics.CreateLogMetricRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_metrics.LogMetric:
            r"""Call the create log metric method over HTTP.

            Args:
                request (~.logging_metrics.CreateLogMetricRequest):
                    The request object. The parameters to CreateLogMetric.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_metrics.LogMetric:
                    Describes a logs-based metric. The
                value of the metric is the number of log
                entries that match a logs filter in a
                given time interval.

                Logs-based metrics can also be used to
                extract values from logs and create a
                distribution of the values. The
                distribution records the statistics of
                the extracted values along with an
                optional histogram of the values as
                specified by the bucket options.

            """

            http_options = _BaseMetricsServiceV2RestTransport._BaseCreateLogMetric._get_http_options()

            request, metadata = self._interceptor.pre_create_log_metric(request, metadata)
            transcoded_request = _BaseMetricsServiceV2RestTransport._BaseCreateLogMetric._get_transcoded_request(http_options, request)

            body = _BaseMetricsServiceV2RestTransport._BaseCreateLogMetric._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseMetricsServiceV2RestTransport._BaseCreateLogMetric._get_query_params_json(transcoded_request)

            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                request_url = "{host}{uri}".format(host=self._host, uri=transcoded_request['uri'])
                method = transcoded_request['method']
                try:
                    request_payload = type(request).to_json(request)
                except:
                    request_payload = None
                http_request = {
                  "payload": request_payload,
                  "requestMethod": method,
                  "requestUrl": request_url,
                  "headers": dict(metadata),
                }
                _LOGGER.debug(
                    f"Sending request for google.logging_v2.MetricsServiceV2Client.CreateLogMetric",
                    extra = {
                        "serviceName": "google.logging.v2.MetricsServiceV2",
                        "rpcName": "CreateLogMetric",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = MetricsServiceV2RestTransport._CreateLogMetric._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_metrics.LogMetric()
            pb_resp = logging_metrics.LogMetric.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_create_log_metric(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_create_log_metric_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_metrics.LogMetric.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.MetricsServiceV2Client.create_log_metric",
                    extra = {
                        "serviceName": "google.logging.v2.MetricsServiceV2",
                        "rpcName": "CreateLogMetric",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _DeleteLogMetric(_BaseMetricsServiceV2RestTransport._BaseDeleteLogMetric, MetricsServiceV2RestStub):
        def __hash__(self):
            return hash("MetricsServiceV2RestTransport.DeleteLogMetric")

        @staticmethod
        def _get_response(
            host,
            metadata,
            query_params,
            session,
            timeout,
            transcoded_request,
            body=None):

            uri = transcoded_request['uri']
            method = transcoded_request['method']
            headers = dict(metadata)
            headers['Content-Type'] = 'application/json'
            response = getattr(session, method)(
                "{host}{uri}".format(host=host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
                )
            return response

        def __call__(self,
                request: logging_metrics.DeleteLogMetricRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ):
            r"""Call the delete log metric method over HTTP.

            Args:
                request (~.logging_metrics.DeleteLogMetricRequest):
                    The request object. The parameters to DeleteLogMetric.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.
            """

            http_options = _BaseMetricsServiceV2RestTransport._BaseDeleteLogMetric._get_http_options()

            request, metadata = self._interceptor.pre_delete_log_metric(request, metadata)
            transcoded_request = _BaseMetricsServiceV2RestTransport._BaseDeleteLogMetric._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseMetricsServiceV2RestTransport._BaseDeleteLogMetric._get_query_params_json(transcoded_request)

            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                request_url = "{host}{uri}".format(host=self._host, uri=transcoded_request['uri'])
                method = transcoded_request['method']
                try:
                    request_payload = json_format.MessageToJson(request)
                except:
                    request_payload = None
                http_request = {
                  "payload": request_payload,
                  "requestMethod": method,
                  "requestUrl": request_url,
                  "headers": dict(metadata),
                }
                _LOGGER.debug(
                    f"Sending request for google.logging_v2.MetricsServiceV2Client.DeleteLogMetric",
                    extra = {
                        "serviceName": "google.logging.v2.MetricsServiceV2",
                        "rpcName": "DeleteLogMetric",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = MetricsServiceV2RestTransport._DeleteLogMetric._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

    class _GetLogMetric(_BaseMetricsServiceV2RestTransport._BaseGetLogMetric, MetricsServiceV2RestStub):
        def __hash__(self):
            return hash("MetricsServiceV2RestTransport.GetLogMetric")

        @staticmethod
        def _get_response(
            host,
            metadata,
            query_params,
            session,
            timeout,
            transcoded_request,
            body=None):

            uri = transcoded_request['uri']
            method = transcoded_request['method']
            headers = dict(metadata)
            headers['Content-Type'] = 'application/json'
            response = getattr(session, method)(
                "{host}{uri}".format(host=host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
                )
            return response

        def __call__(self,
                request: logging_metrics.GetLogMetricRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_metrics.LogMetric:
            r"""Call the get log metric method over HTTP.

            Args:
                request (~.logging_metrics.GetLogMetricRequest):
                    The request object. The parameters to GetLogMetric.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_metrics.LogMetric:
                    Describes a logs-based metric. The
                value of the metric is the number of log
                entries that match a logs filter in a
                given time interval.

                Logs-based metrics can also be used to
                extract values from logs and create a
                distribution of the values. The
                distribution records the statistics of
                the extracted values along with an
                optional histogram of the values as
                specified by the bucket options.

            """

            http_options = _BaseMetricsServiceV2RestTransport._BaseGetLogMetric._get_http_options()

            request, metadata = self._interceptor.pre_get_log_metric(request, metadata)
            transcoded_request = _BaseMetricsServiceV2RestTransport._BaseGetLogMetric._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseMetricsServiceV2RestTransport._BaseGetLogMetric._get_query_params_json(transcoded_request)

            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                request_url = "{host}{uri}".format(host=self._host, uri=transcoded_request['uri'])
                method = transcoded_request['method']
                try:
                    request_payload = type(request).to_json(request)
                except:
                    request_payload = None
                http_request = {
                  "payload": request_payload,
                  "requestMethod": method,
                  "requestUrl": request_url,
                  "headers": dict(metadata),
                }
                _LOGGER.debug(
                    f"Sending request for google.logging_v2.MetricsServiceV2Client.GetLogMetric",
                    extra = {
                        "serviceName": "google.logging.v2.MetricsServiceV2",
                        "rpcName": "GetLogMetric",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = MetricsServiceV2RestTransport._GetLogMetric._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_metrics.LogMetric()
            pb_resp = logging_metrics.LogMetric.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_get_log_metric(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_get_log_metric_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_metrics.LogMetric.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.MetricsServiceV2Client.get_log_metric",
                    extra = {
                        "serviceName": "google.logging.v2.MetricsServiceV2",
                        "rpcName": "GetLogMetric",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _ListLogMetrics(_BaseMetricsServiceV2RestTransport._BaseListLogMetrics, MetricsServiceV2RestStub):
        def __hash__(self):
            return hash("MetricsServiceV2RestTransport.ListLogMetrics")

        @staticmethod
        def _get_response(
            host,
            metadata,
            query_params,
            session,
            timeout,
            transcoded_request,
            body=None):

            uri = transcoded_request['uri']
            method = transcoded_request['method']
            headers = dict(metadata)
            headers['Content-Type'] = 'application/json'
            response = getattr(session, method)(
                "{host}{uri}".format(host=host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
                )
            return response

        def __call__(self,
                request: logging_metrics.ListLogMetricsRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_metrics.ListLogMetricsResponse:
            r"""Call the list log metrics method over HTTP.

            Args:
                request (~.logging_metrics.ListLogMetricsRequest):
                    The request object. The parameters to ListLogMetrics.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_metrics.ListLogMetricsResponse:
                    Result returned from ListLogMetrics.
            """

            http_options = _BaseMetricsServiceV2RestTransport._BaseListLogMetrics._get_http_options()

            request, metadata = self._interceptor.pre_list_log_metrics(request, metadata)
            transcoded_request = _BaseMetricsServiceV2RestTransport._BaseListLogMetrics._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseMetricsServiceV2RestTransport._BaseListLogMetrics._get_query_params_json(transcoded_request)

            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                request_url = "{host}{uri}".format(host=self._host, uri=transcoded_request['uri'])
                method = transcoded_request['method']
                try:
                    request_payload = type(request).to_json(request)
                except:
                    request_payload = None
                http_request = {
                  "payload": request_payload,
                  "requestMethod": method,
                  "requestUrl": request_url,
                  "headers": dict(metadata),
                }
                _LOGGER.debug(
                    f"Sending request for google.logging_v2.MetricsServiceV2Client.ListLogMetrics",
                    extra = {
                        "serviceName": "google.logging.v2.MetricsServiceV2",
                        "rpcName": "ListLogMetrics",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = MetricsServiceV2RestTransport._ListLogMetrics._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_metrics.ListLogMetricsResponse()
            pb_resp = logging_metrics.ListLogMetricsResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_log_metrics(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_log_metrics_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_metrics.ListLogMetricsResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.MetricsServiceV2Client.list_log_metrics",
                    extra = {
                        "serviceName": "google.logging.v2.MetricsServiceV2",
                        "rpcName": "ListLogMetrics",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _UpdateLogMetric(_BaseMetricsServiceV2RestTransport._BaseUpdateLogMetric, MetricsServiceV2RestStub):
        def __hash__(self):
            return hash("MetricsServiceV2RestTransport.UpdateLogMetric")

        @staticmethod
        def _get_response(
            host,
            metadata,
            query_params,
            session,
            timeout,
            transcoded_request,
            body=None):

            uri = transcoded_request['uri']
            method = transcoded_request['method']
            headers = dict(metadata)
            headers['Content-Type'] = 'application/json'
            response = getattr(session, method)(
                "{host}{uri}".format(host=host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
                data=body,
                )
            return response

        def __call__(self,
                request: logging_metrics.UpdateLogMetricRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_metrics.LogMetric:
            r"""Call the update log metric method over HTTP.

            Args:
                request (~.logging_metrics.UpdateLogMetricRequest):
                    The request object. The parameters to UpdateLogMetric.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_metrics.LogMetric:
                    Describes a logs-based metric. The
                value of the metric is the number of log
                entries that match a logs filter in a
                given time interval.

                Logs-based metrics can also be used to
                extract values from logs and create a
                distribution of the values. The
                distribution records the statistics of
                the extracted values along with an
                optional histogram of the values as
                specified by the bucket options.

            """

            http_options = _BaseMetricsServiceV2RestTransport._BaseUpdateLogMetric._get_http_options()

            request, metadata = self._interceptor.pre_update_log_metric(request, metadata)
            transcoded_request = _BaseMetricsServiceV2RestTransport._BaseUpdateLogMetric._get_transcoded_request(http_options, request)

            body = _BaseMetricsServiceV2RestTransport._BaseUpdateLogMetric._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseMetricsServiceV2RestTransport._BaseUpdateLogMetric._get_query_params_json(transcoded_request)

            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                request_url = "{host}{uri}".format(host=self._host, uri=transcoded_request['uri'])
                method = transcoded_request['method']
                try:
                    request_payload = type(request).to_json(request)
                except:
                    request_payload = None
                http_request = {
                  "payload": request_payload,
                  "requestMethod": method,
                  "requestUrl": request_url,
                  "headers": dict(metadata),
                }
                _LOGGER.debug(
                    f"Sending request for google.logging_v2.MetricsServiceV2Client.UpdateLogMetric",
                    extra = {
                        "serviceName": "google.logging.v2.MetricsServiceV2",
                        "rpcName": "UpdateLogMetric",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = MetricsServiceV2RestTransport._UpdateLogMetric._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_metrics.LogMetric()
            pb_resp = logging_metrics.LogMetric.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_update_log_metric(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_update_log_metric_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_metrics.LogMetric.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.MetricsServiceV2Client.update_log_metric",
                    extra = {
                        "serviceName": "google.logging.v2.MetricsServiceV2",
                        "rpcName": "UpdateLogMetric",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    @property
    def create_log_metric(self) -> Callable[
            [logging_metrics.CreateLogMetricRequest],
            logging_metrics.LogMetric]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CreateLogMetric(self._session, self._host, self._interceptor) # type: ignore

    @property
    def delete_log_metric(self) -> Callable[
            [logging_metrics.DeleteLogMetricRequest],
            empty_pb2.Empty]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteLogMetric(self._session, self._host, self._interceptor) # type: ignore

    @property
    def get_log_metric(self) -> Callable[
            [logging_metrics.GetLogMetricRequest],
            logging_metrics.LogMetric]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetLogMetric(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_log_metrics(self) -> Callable[
            [logging_metrics.ListLogMetricsRequest],
            logging_metrics.ListLogMetricsResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListLogMetrics(self._session, self._host, self._interceptor) # type: ignore

    @property
    def update_log_metric(self) -> Callable[
            [logging_metrics.UpdateLogMetricRequest],
            logging_metrics.LogMetric]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UpdateLogMetric(self._session, self._host, self._interceptor) # type: ignore

    @property
    def kind(self) -> str:
        return "rest"

    def close(self):
        self._session.close()


__all__=(
    'MetricsServiceV2RestTransport',
)
