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
import logging as std_logging
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
from googlecloudsdk.generated_clients.gapic_clients.logging_v2.types import logging


from .rest_base import _BaseLoggingServiceV2RestTransport
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

_LOGGER = std_logging.getLogger(__name__)

DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(
    gapic_version=BASE_DEFAULT_CLIENT_INFO.gapic_version,
    grpc_version=None,
    rest_version=f"requests@{requests_version}",
)

if hasattr(DEFAULT_CLIENT_INFO, "protobuf_runtime_version"):  # pragma: NO COVER
    DEFAULT_CLIENT_INFO.protobuf_runtime_version = cloudsdk.google.protobuf.__version__


class LoggingServiceV2RestInterceptor:
    """Interceptor for LoggingServiceV2.

    Interceptors are used to manipulate requests, request metadata, and responses
    in arbitrary ways.
    Example use cases include:
    * Logging
    * Verifying requests according to service or custom semantics
    * Stripping extraneous information from responses

    These use cases and more can be enabled by injecting an
    instance of a custom subclass when constructing the LoggingServiceV2RestTransport.

    .. code-block:: python
        class MyCustomLoggingServiceV2Interceptor(LoggingServiceV2RestInterceptor):
            def pre_delete_log(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def pre_list_log_entries(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_log_entries(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_logs(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_logs(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_monitored_resource_descriptors(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_monitored_resource_descriptors(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_write_log_entries(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_write_log_entries(self, response):
                logging.log(f"Received response: {response}")
                return response

        transport = LoggingServiceV2RestTransport(interceptor=MyCustomLoggingServiceV2Interceptor())
        client = LoggingServiceV2Client(transport=transport)


    """
    def pre_delete_log(self, request: logging.DeleteLogRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging.DeleteLogRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for delete_log

        Override in a subclass to manipulate the request or metadata
        before they are sent to the LoggingServiceV2 server.
        """
        return request, metadata

    def pre_list_log_entries(self, request: logging.ListLogEntriesRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging.ListLogEntriesRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_log_entries

        Override in a subclass to manipulate the request or metadata
        before they are sent to the LoggingServiceV2 server.
        """
        return request, metadata

    def post_list_log_entries(self, response: logging.ListLogEntriesResponse) -> logging.ListLogEntriesResponse:
        """Post-rpc interceptor for list_log_entries

        DEPRECATED. Please use the `post_list_log_entries_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the LoggingServiceV2 server but before
        it is returned to user code. This `post_list_log_entries` interceptor runs
        before the `post_list_log_entries_with_metadata` interceptor.
        """
        return response

    def post_list_log_entries_with_metadata(self, response: logging.ListLogEntriesResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging.ListLogEntriesResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_log_entries

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the LoggingServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_log_entries_with_metadata`
        interceptor in new development instead of the `post_list_log_entries` interceptor.
        When both interceptors are used, this `post_list_log_entries_with_metadata` interceptor runs after the
        `post_list_log_entries` interceptor. The (possibly modified) response returned by
        `post_list_log_entries` will be passed to
        `post_list_log_entries_with_metadata`.
        """
        return response, metadata

    def pre_list_logs(self, request: logging.ListLogsRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging.ListLogsRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_logs

        Override in a subclass to manipulate the request or metadata
        before they are sent to the LoggingServiceV2 server.
        """
        return request, metadata

    def post_list_logs(self, response: logging.ListLogsResponse) -> logging.ListLogsResponse:
        """Post-rpc interceptor for list_logs

        DEPRECATED. Please use the `post_list_logs_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the LoggingServiceV2 server but before
        it is returned to user code. This `post_list_logs` interceptor runs
        before the `post_list_logs_with_metadata` interceptor.
        """
        return response

    def post_list_logs_with_metadata(self, response: logging.ListLogsResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging.ListLogsResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_logs

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the LoggingServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_logs_with_metadata`
        interceptor in new development instead of the `post_list_logs` interceptor.
        When both interceptors are used, this `post_list_logs_with_metadata` interceptor runs after the
        `post_list_logs` interceptor. The (possibly modified) response returned by
        `post_list_logs` will be passed to
        `post_list_logs_with_metadata`.
        """
        return response, metadata

    def pre_list_monitored_resource_descriptors(self, request: logging.ListMonitoredResourceDescriptorsRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging.ListMonitoredResourceDescriptorsRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_monitored_resource_descriptors

        Override in a subclass to manipulate the request or metadata
        before they are sent to the LoggingServiceV2 server.
        """
        return request, metadata

    def post_list_monitored_resource_descriptors(self, response: logging.ListMonitoredResourceDescriptorsResponse) -> logging.ListMonitoredResourceDescriptorsResponse:
        """Post-rpc interceptor for list_monitored_resource_descriptors

        DEPRECATED. Please use the `post_list_monitored_resource_descriptors_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the LoggingServiceV2 server but before
        it is returned to user code. This `post_list_monitored_resource_descriptors` interceptor runs
        before the `post_list_monitored_resource_descriptors_with_metadata` interceptor.
        """
        return response

    def post_list_monitored_resource_descriptors_with_metadata(self, response: logging.ListMonitoredResourceDescriptorsResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging.ListMonitoredResourceDescriptorsResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_monitored_resource_descriptors

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the LoggingServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_monitored_resource_descriptors_with_metadata`
        interceptor in new development instead of the `post_list_monitored_resource_descriptors` interceptor.
        When both interceptors are used, this `post_list_monitored_resource_descriptors_with_metadata` interceptor runs after the
        `post_list_monitored_resource_descriptors` interceptor. The (possibly modified) response returned by
        `post_list_monitored_resource_descriptors` will be passed to
        `post_list_monitored_resource_descriptors_with_metadata`.
        """
        return response, metadata

    def pre_write_log_entries(self, request: logging.WriteLogEntriesRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging.WriteLogEntriesRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for write_log_entries

        Override in a subclass to manipulate the request or metadata
        before they are sent to the LoggingServiceV2 server.
        """
        return request, metadata

    def post_write_log_entries(self, response: logging.WriteLogEntriesResponse) -> logging.WriteLogEntriesResponse:
        """Post-rpc interceptor for write_log_entries

        DEPRECATED. Please use the `post_write_log_entries_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the LoggingServiceV2 server but before
        it is returned to user code. This `post_write_log_entries` interceptor runs
        before the `post_write_log_entries_with_metadata` interceptor.
        """
        return response

    def post_write_log_entries_with_metadata(self, response: logging.WriteLogEntriesResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging.WriteLogEntriesResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for write_log_entries

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the LoggingServiceV2 server but before it is returned to user code.

        We recommend only using this `post_write_log_entries_with_metadata`
        interceptor in new development instead of the `post_write_log_entries` interceptor.
        When both interceptors are used, this `post_write_log_entries_with_metadata` interceptor runs after the
        `post_write_log_entries` interceptor. The (possibly modified) response returned by
        `post_write_log_entries` will be passed to
        `post_write_log_entries_with_metadata`.
        """
        return response, metadata


@dataclasses.dataclass
class LoggingServiceV2RestStub:
    _session: AuthorizedSession
    _host: str
    _interceptor: LoggingServiceV2RestInterceptor


class LoggingServiceV2RestTransport(_BaseLoggingServiceV2RestTransport):
    """REST backend synchronous transport for LoggingServiceV2.

    Service for storing and querying logs.

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
            interceptor: Optional[LoggingServiceV2RestInterceptor] = None,
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
        self._interceptor = interceptor or LoggingServiceV2RestInterceptor()
        self._prep_wrapped_messages(client_info)

    class _DeleteLog(_BaseLoggingServiceV2RestTransport._BaseDeleteLog, LoggingServiceV2RestStub):
        def __hash__(self):
            return hash("LoggingServiceV2RestTransport.DeleteLog")

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
                request: logging.DeleteLogRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ):
            r"""Call the delete log method over HTTP.

            Args:
                request (~.logging.DeleteLogRequest):
                    The request object. The parameters to DeleteLog.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.
            """

            http_options = _BaseLoggingServiceV2RestTransport._BaseDeleteLog._get_http_options()

            request, metadata = self._interceptor.pre_delete_log(request, metadata)
            transcoded_request = _BaseLoggingServiceV2RestTransport._BaseDeleteLog._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseLoggingServiceV2RestTransport._BaseDeleteLog._get_query_params_json(transcoded_request)

            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(std_logging.DEBUG):  # pragma: NO COVER
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
                    f"Sending request for google.logging_v2.LoggingServiceV2Client.DeleteLog",
                    extra = {
                        "serviceName": "google.logging.v2.LoggingServiceV2",
                        "rpcName": "DeleteLog",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = LoggingServiceV2RestTransport._DeleteLog._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

    class _ListLogEntries(_BaseLoggingServiceV2RestTransport._BaseListLogEntries, LoggingServiceV2RestStub):
        def __hash__(self):
            return hash("LoggingServiceV2RestTransport.ListLogEntries")

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
                request: logging.ListLogEntriesRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging.ListLogEntriesResponse:
            r"""Call the list log entries method over HTTP.

            Args:
                request (~.logging.ListLogEntriesRequest):
                    The request object. The parameters to ``ListLogEntries``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging.ListLogEntriesResponse:
                    Result returned from ``ListLogEntries``.
            """

            http_options = _BaseLoggingServiceV2RestTransport._BaseListLogEntries._get_http_options()

            request, metadata = self._interceptor.pre_list_log_entries(request, metadata)
            transcoded_request = _BaseLoggingServiceV2RestTransport._BaseListLogEntries._get_transcoded_request(http_options, request)

            body = _BaseLoggingServiceV2RestTransport._BaseListLogEntries._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseLoggingServiceV2RestTransport._BaseListLogEntries._get_query_params_json(transcoded_request)

            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(std_logging.DEBUG):  # pragma: NO COVER
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
                    f"Sending request for google.logging_v2.LoggingServiceV2Client.ListLogEntries",
                    extra = {
                        "serviceName": "google.logging.v2.LoggingServiceV2",
                        "rpcName": "ListLogEntries",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = LoggingServiceV2RestTransport._ListLogEntries._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging.ListLogEntriesResponse()
            pb_resp = logging.ListLogEntriesResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_log_entries(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_log_entries_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(std_logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging.ListLogEntriesResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.LoggingServiceV2Client.list_log_entries",
                    extra = {
                        "serviceName": "google.logging.v2.LoggingServiceV2",
                        "rpcName": "ListLogEntries",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _ListLogs(_BaseLoggingServiceV2RestTransport._BaseListLogs, LoggingServiceV2RestStub):
        def __hash__(self):
            return hash("LoggingServiceV2RestTransport.ListLogs")

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
                request: logging.ListLogsRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging.ListLogsResponse:
            r"""Call the list logs method over HTTP.

            Args:
                request (~.logging.ListLogsRequest):
                    The request object. The parameters to ListLogs.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging.ListLogsResponse:
                    Result returned from ListLogs.
            """

            http_options = _BaseLoggingServiceV2RestTransport._BaseListLogs._get_http_options()

            request, metadata = self._interceptor.pre_list_logs(request, metadata)
            transcoded_request = _BaseLoggingServiceV2RestTransport._BaseListLogs._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseLoggingServiceV2RestTransport._BaseListLogs._get_query_params_json(transcoded_request)

            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(std_logging.DEBUG):  # pragma: NO COVER
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
                    f"Sending request for google.logging_v2.LoggingServiceV2Client.ListLogs",
                    extra = {
                        "serviceName": "google.logging.v2.LoggingServiceV2",
                        "rpcName": "ListLogs",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = LoggingServiceV2RestTransport._ListLogs._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging.ListLogsResponse()
            pb_resp = logging.ListLogsResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_logs(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_logs_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(std_logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging.ListLogsResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.LoggingServiceV2Client.list_logs",
                    extra = {
                        "serviceName": "google.logging.v2.LoggingServiceV2",
                        "rpcName": "ListLogs",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _ListMonitoredResourceDescriptors(_BaseLoggingServiceV2RestTransport._BaseListMonitoredResourceDescriptors, LoggingServiceV2RestStub):
        def __hash__(self):
            return hash("LoggingServiceV2RestTransport.ListMonitoredResourceDescriptors")

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
                request: logging.ListMonitoredResourceDescriptorsRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging.ListMonitoredResourceDescriptorsResponse:
            r"""Call the list monitored resource
        descriptors method over HTTP.

            Args:
                request (~.logging.ListMonitoredResourceDescriptorsRequest):
                    The request object. The parameters to
                ListMonitoredResourceDescriptors
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging.ListMonitoredResourceDescriptorsResponse:
                    Result returned from
                ListMonitoredResourceDescriptors.

            """

            http_options = _BaseLoggingServiceV2RestTransport._BaseListMonitoredResourceDescriptors._get_http_options()

            request, metadata = self._interceptor.pre_list_monitored_resource_descriptors(request, metadata)
            transcoded_request = _BaseLoggingServiceV2RestTransport._BaseListMonitoredResourceDescriptors._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseLoggingServiceV2RestTransport._BaseListMonitoredResourceDescriptors._get_query_params_json(transcoded_request)

            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(std_logging.DEBUG):  # pragma: NO COVER
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
                    f"Sending request for google.logging_v2.LoggingServiceV2Client.ListMonitoredResourceDescriptors",
                    extra = {
                        "serviceName": "google.logging.v2.LoggingServiceV2",
                        "rpcName": "ListMonitoredResourceDescriptors",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = LoggingServiceV2RestTransport._ListMonitoredResourceDescriptors._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging.ListMonitoredResourceDescriptorsResponse()
            pb_resp = logging.ListMonitoredResourceDescriptorsResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_monitored_resource_descriptors(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_monitored_resource_descriptors_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(std_logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging.ListMonitoredResourceDescriptorsResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.LoggingServiceV2Client.list_monitored_resource_descriptors",
                    extra = {
                        "serviceName": "google.logging.v2.LoggingServiceV2",
                        "rpcName": "ListMonitoredResourceDescriptors",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _TailLogEntries(_BaseLoggingServiceV2RestTransport._BaseTailLogEntries, LoggingServiceV2RestStub):
        def __hash__(self):
            return hash("LoggingServiceV2RestTransport.TailLogEntries")

        def __call__(self,
                request: logging.TailLogEntriesRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> rest_streaming.ResponseIterator:
            raise NotImplementedError(
                "Method TailLogEntries is not available over REST transport"
            )
    class _WriteLogEntries(_BaseLoggingServiceV2RestTransport._BaseWriteLogEntries, LoggingServiceV2RestStub):
        def __hash__(self):
            return hash("LoggingServiceV2RestTransport.WriteLogEntries")

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
                request: logging.WriteLogEntriesRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging.WriteLogEntriesResponse:
            r"""Call the write log entries method over HTTP.

            Args:
                request (~.logging.WriteLogEntriesRequest):
                    The request object. The parameters to WriteLogEntries.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging.WriteLogEntriesResponse:
                    Result returned from WriteLogEntries.
            """

            http_options = _BaseLoggingServiceV2RestTransport._BaseWriteLogEntries._get_http_options()

            request, metadata = self._interceptor.pre_write_log_entries(request, metadata)
            transcoded_request = _BaseLoggingServiceV2RestTransport._BaseWriteLogEntries._get_transcoded_request(http_options, request)

            body = _BaseLoggingServiceV2RestTransport._BaseWriteLogEntries._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseLoggingServiceV2RestTransport._BaseWriteLogEntries._get_query_params_json(transcoded_request)

            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(std_logging.DEBUG):  # pragma: NO COVER
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
                    f"Sending request for google.logging_v2.LoggingServiceV2Client.WriteLogEntries",
                    extra = {
                        "serviceName": "google.logging.v2.LoggingServiceV2",
                        "rpcName": "WriteLogEntries",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = LoggingServiceV2RestTransport._WriteLogEntries._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging.WriteLogEntriesResponse()
            pb_resp = logging.WriteLogEntriesResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_write_log_entries(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_write_log_entries_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(std_logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging.WriteLogEntriesResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.LoggingServiceV2Client.write_log_entries",
                    extra = {
                        "serviceName": "google.logging.v2.LoggingServiceV2",
                        "rpcName": "WriteLogEntries",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    @property
    def delete_log(self) -> Callable[
            [logging.DeleteLogRequest],
            empty_pb2.Empty]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteLog(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_log_entries(self) -> Callable[
            [logging.ListLogEntriesRequest],
            logging.ListLogEntriesResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListLogEntries(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_logs(self) -> Callable[
            [logging.ListLogsRequest],
            logging.ListLogsResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListLogs(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_monitored_resource_descriptors(self) -> Callable[
            [logging.ListMonitoredResourceDescriptorsRequest],
            logging.ListMonitoredResourceDescriptorsResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListMonitoredResourceDescriptors(self._session, self._host, self._interceptor) # type: ignore

    @property
    def tail_log_entries(self) -> Callable[
            [logging.TailLogEntriesRequest],
            logging.TailLogEntriesResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._TailLogEntries(self._session, self._host, self._interceptor) # type: ignore

    @property
    def write_log_entries(self) -> Callable[
            [logging.WriteLogEntriesRequest],
            logging.WriteLogEntriesResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._WriteLogEntries(self._session, self._host, self._interceptor) # type: ignore

    @property
    def kind(self) -> str:
        return "rest"

    def close(self):
        self._session.close()


__all__=(
    'LoggingServiceV2RestTransport',
)
