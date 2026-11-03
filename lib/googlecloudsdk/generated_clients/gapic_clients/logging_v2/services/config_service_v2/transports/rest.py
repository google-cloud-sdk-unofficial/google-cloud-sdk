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
from google.api_core import operations_v1

from requests import __version__ as requests_version
import dataclasses
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import warnings


from cloudsdk.google.protobuf import empty_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.logging_v2.types import logging_config
from google.longrunning import operations_pb2  # type: ignore


from .rest_base import _BaseConfigServiceV2RestTransport
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


class ConfigServiceV2RestInterceptor:
    """Interceptor for ConfigServiceV2.

    Interceptors are used to manipulate requests, request metadata, and responses
    in arbitrary ways.
    Example use cases include:
    * Logging
    * Verifying requests according to service or custom semantics
    * Stripping extraneous information from responses

    These use cases and more can be enabled by injecting an
    instance of a custom subclass when constructing the ConfigServiceV2RestTransport.

    .. code-block:: python
        class MyCustomConfigServiceV2Interceptor(ConfigServiceV2RestInterceptor):
            def pre_copy_log_entries(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_copy_log_entries(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_create_bucket(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_create_bucket(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_create_bucket_async(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_create_bucket_async(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_create_exclusion(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_create_exclusion(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_create_link(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_create_link(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_create_log_scope(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_create_log_scope(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_create_saved_query(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_create_saved_query(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_create_sink(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_create_sink(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_create_view(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_create_view(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_delete_bucket(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def pre_delete_exclusion(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def pre_delete_link(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_delete_link(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_delete_log_scope(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def pre_delete_saved_query(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def pre_delete_sink(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def pre_delete_view(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def pre_get_bucket(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_bucket(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_get_cmek_settings(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_cmek_settings(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_get_exclusion(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_exclusion(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_get_link(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_link(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_get_log_scope(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_log_scope(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_get_saved_query(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_saved_query(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_get_settings(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_settings(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_get_sink(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_sink(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_get_view(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_view(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_buckets(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_buckets(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_exclusions(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_exclusions(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_links(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_links(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_log_scopes(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_log_scopes(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_recent_queries(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_recent_queries(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_saved_queries(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_saved_queries(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_sinks(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_sinks(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_views(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_views(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_undelete_bucket(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def pre_update_bucket(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_update_bucket(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_update_bucket_async(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_update_bucket_async(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_update_cmek_settings(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_update_cmek_settings(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_update_exclusion(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_update_exclusion(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_update_log_scope(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_update_log_scope(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_update_saved_query(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_update_saved_query(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_update_settings(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_update_settings(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_update_sink(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_update_sink(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_update_view(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_update_view(self, response):
                logging.log(f"Received response: {response}")
                return response

        transport = ConfigServiceV2RestTransport(interceptor=MyCustomConfigServiceV2Interceptor())
        client = ConfigServiceV2Client(transport=transport)


    """
    def pre_copy_log_entries(self, request: logging_config.CopyLogEntriesRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.CopyLogEntriesRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for copy_log_entries

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_copy_log_entries(self, response: operations_pb2.Operation) -> operations_pb2.Operation:
        """Post-rpc interceptor for copy_log_entries

        DEPRECATED. Please use the `post_copy_log_entries_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_copy_log_entries` interceptor runs
        before the `post_copy_log_entries_with_metadata` interceptor.
        """
        return response

    def post_copy_log_entries_with_metadata(self, response: operations_pb2.Operation, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[operations_pb2.Operation, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for copy_log_entries

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_copy_log_entries_with_metadata`
        interceptor in new development instead of the `post_copy_log_entries` interceptor.
        When both interceptors are used, this `post_copy_log_entries_with_metadata` interceptor runs after the
        `post_copy_log_entries` interceptor. The (possibly modified) response returned by
        `post_copy_log_entries` will be passed to
        `post_copy_log_entries_with_metadata`.
        """
        return response, metadata

    def pre_create_bucket(self, request: logging_config.CreateBucketRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.CreateBucketRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for create_bucket

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_create_bucket(self, response: logging_config.LogBucket) -> logging_config.LogBucket:
        """Post-rpc interceptor for create_bucket

        DEPRECATED. Please use the `post_create_bucket_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_create_bucket` interceptor runs
        before the `post_create_bucket_with_metadata` interceptor.
        """
        return response

    def post_create_bucket_with_metadata(self, response: logging_config.LogBucket, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogBucket, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for create_bucket

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_create_bucket_with_metadata`
        interceptor in new development instead of the `post_create_bucket` interceptor.
        When both interceptors are used, this `post_create_bucket_with_metadata` interceptor runs after the
        `post_create_bucket` interceptor. The (possibly modified) response returned by
        `post_create_bucket` will be passed to
        `post_create_bucket_with_metadata`.
        """
        return response, metadata

    def pre_create_bucket_async(self, request: logging_config.CreateBucketRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.CreateBucketRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for create_bucket_async

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_create_bucket_async(self, response: operations_pb2.Operation) -> operations_pb2.Operation:
        """Post-rpc interceptor for create_bucket_async

        DEPRECATED. Please use the `post_create_bucket_async_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_create_bucket_async` interceptor runs
        before the `post_create_bucket_async_with_metadata` interceptor.
        """
        return response

    def post_create_bucket_async_with_metadata(self, response: operations_pb2.Operation, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[operations_pb2.Operation, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for create_bucket_async

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_create_bucket_async_with_metadata`
        interceptor in new development instead of the `post_create_bucket_async` interceptor.
        When both interceptors are used, this `post_create_bucket_async_with_metadata` interceptor runs after the
        `post_create_bucket_async` interceptor. The (possibly modified) response returned by
        `post_create_bucket_async` will be passed to
        `post_create_bucket_async_with_metadata`.
        """
        return response, metadata

    def pre_create_exclusion(self, request: logging_config.CreateExclusionRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.CreateExclusionRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for create_exclusion

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_create_exclusion(self, response: logging_config.LogExclusion) -> logging_config.LogExclusion:
        """Post-rpc interceptor for create_exclusion

        DEPRECATED. Please use the `post_create_exclusion_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_create_exclusion` interceptor runs
        before the `post_create_exclusion_with_metadata` interceptor.
        """
        return response

    def post_create_exclusion_with_metadata(self, response: logging_config.LogExclusion, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogExclusion, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for create_exclusion

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_create_exclusion_with_metadata`
        interceptor in new development instead of the `post_create_exclusion` interceptor.
        When both interceptors are used, this `post_create_exclusion_with_metadata` interceptor runs after the
        `post_create_exclusion` interceptor. The (possibly modified) response returned by
        `post_create_exclusion` will be passed to
        `post_create_exclusion_with_metadata`.
        """
        return response, metadata

    def pre_create_link(self, request: logging_config.CreateLinkRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.CreateLinkRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for create_link

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_create_link(self, response: operations_pb2.Operation) -> operations_pb2.Operation:
        """Post-rpc interceptor for create_link

        DEPRECATED. Please use the `post_create_link_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_create_link` interceptor runs
        before the `post_create_link_with_metadata` interceptor.
        """
        return response

    def post_create_link_with_metadata(self, response: operations_pb2.Operation, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[operations_pb2.Operation, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for create_link

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_create_link_with_metadata`
        interceptor in new development instead of the `post_create_link` interceptor.
        When both interceptors are used, this `post_create_link_with_metadata` interceptor runs after the
        `post_create_link` interceptor. The (possibly modified) response returned by
        `post_create_link` will be passed to
        `post_create_link_with_metadata`.
        """
        return response, metadata

    def pre_create_log_scope(self, request: logging_config.CreateLogScopeRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.CreateLogScopeRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for create_log_scope

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_create_log_scope(self, response: logging_config.LogScope) -> logging_config.LogScope:
        """Post-rpc interceptor for create_log_scope

        DEPRECATED. Please use the `post_create_log_scope_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_create_log_scope` interceptor runs
        before the `post_create_log_scope_with_metadata` interceptor.
        """
        return response

    def post_create_log_scope_with_metadata(self, response: logging_config.LogScope, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogScope, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for create_log_scope

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_create_log_scope_with_metadata`
        interceptor in new development instead of the `post_create_log_scope` interceptor.
        When both interceptors are used, this `post_create_log_scope_with_metadata` interceptor runs after the
        `post_create_log_scope` interceptor. The (possibly modified) response returned by
        `post_create_log_scope` will be passed to
        `post_create_log_scope_with_metadata`.
        """
        return response, metadata

    def pre_create_saved_query(self, request: logging_config.CreateSavedQueryRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.CreateSavedQueryRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for create_saved_query

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_create_saved_query(self, response: logging_config.SavedQuery) -> logging_config.SavedQuery:
        """Post-rpc interceptor for create_saved_query

        DEPRECATED. Please use the `post_create_saved_query_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_create_saved_query` interceptor runs
        before the `post_create_saved_query_with_metadata` interceptor.
        """
        return response

    def post_create_saved_query_with_metadata(self, response: logging_config.SavedQuery, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.SavedQuery, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for create_saved_query

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_create_saved_query_with_metadata`
        interceptor in new development instead of the `post_create_saved_query` interceptor.
        When both interceptors are used, this `post_create_saved_query_with_metadata` interceptor runs after the
        `post_create_saved_query` interceptor. The (possibly modified) response returned by
        `post_create_saved_query` will be passed to
        `post_create_saved_query_with_metadata`.
        """
        return response, metadata

    def pre_create_sink(self, request: logging_config.CreateSinkRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.CreateSinkRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for create_sink

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_create_sink(self, response: logging_config.LogSink) -> logging_config.LogSink:
        """Post-rpc interceptor for create_sink

        DEPRECATED. Please use the `post_create_sink_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_create_sink` interceptor runs
        before the `post_create_sink_with_metadata` interceptor.
        """
        return response

    def post_create_sink_with_metadata(self, response: logging_config.LogSink, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogSink, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for create_sink

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_create_sink_with_metadata`
        interceptor in new development instead of the `post_create_sink` interceptor.
        When both interceptors are used, this `post_create_sink_with_metadata` interceptor runs after the
        `post_create_sink` interceptor. The (possibly modified) response returned by
        `post_create_sink` will be passed to
        `post_create_sink_with_metadata`.
        """
        return response, metadata

    def pre_create_view(self, request: logging_config.CreateViewRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.CreateViewRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for create_view

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_create_view(self, response: logging_config.LogView) -> logging_config.LogView:
        """Post-rpc interceptor for create_view

        DEPRECATED. Please use the `post_create_view_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_create_view` interceptor runs
        before the `post_create_view_with_metadata` interceptor.
        """
        return response

    def post_create_view_with_metadata(self, response: logging_config.LogView, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogView, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for create_view

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_create_view_with_metadata`
        interceptor in new development instead of the `post_create_view` interceptor.
        When both interceptors are used, this `post_create_view_with_metadata` interceptor runs after the
        `post_create_view` interceptor. The (possibly modified) response returned by
        `post_create_view` will be passed to
        `post_create_view_with_metadata`.
        """
        return response, metadata

    def pre_delete_bucket(self, request: logging_config.DeleteBucketRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.DeleteBucketRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for delete_bucket

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def pre_delete_exclusion(self, request: logging_config.DeleteExclusionRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.DeleteExclusionRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for delete_exclusion

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def pre_delete_link(self, request: logging_config.DeleteLinkRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.DeleteLinkRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for delete_link

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_delete_link(self, response: operations_pb2.Operation) -> operations_pb2.Operation:
        """Post-rpc interceptor for delete_link

        DEPRECATED. Please use the `post_delete_link_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_delete_link` interceptor runs
        before the `post_delete_link_with_metadata` interceptor.
        """
        return response

    def post_delete_link_with_metadata(self, response: operations_pb2.Operation, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[operations_pb2.Operation, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for delete_link

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_delete_link_with_metadata`
        interceptor in new development instead of the `post_delete_link` interceptor.
        When both interceptors are used, this `post_delete_link_with_metadata` interceptor runs after the
        `post_delete_link` interceptor. The (possibly modified) response returned by
        `post_delete_link` will be passed to
        `post_delete_link_with_metadata`.
        """
        return response, metadata

    def pre_delete_log_scope(self, request: logging_config.DeleteLogScopeRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.DeleteLogScopeRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for delete_log_scope

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def pre_delete_saved_query(self, request: logging_config.DeleteSavedQueryRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.DeleteSavedQueryRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for delete_saved_query

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def pre_delete_sink(self, request: logging_config.DeleteSinkRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.DeleteSinkRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for delete_sink

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def pre_delete_view(self, request: logging_config.DeleteViewRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.DeleteViewRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for delete_view

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def pre_get_bucket(self, request: logging_config.GetBucketRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.GetBucketRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for get_bucket

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_get_bucket(self, response: logging_config.LogBucket) -> logging_config.LogBucket:
        """Post-rpc interceptor for get_bucket

        DEPRECATED. Please use the `post_get_bucket_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_get_bucket` interceptor runs
        before the `post_get_bucket_with_metadata` interceptor.
        """
        return response

    def post_get_bucket_with_metadata(self, response: logging_config.LogBucket, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogBucket, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for get_bucket

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_get_bucket_with_metadata`
        interceptor in new development instead of the `post_get_bucket` interceptor.
        When both interceptors are used, this `post_get_bucket_with_metadata` interceptor runs after the
        `post_get_bucket` interceptor. The (possibly modified) response returned by
        `post_get_bucket` will be passed to
        `post_get_bucket_with_metadata`.
        """
        return response, metadata

    def pre_get_cmek_settings(self, request: logging_config.GetCmekSettingsRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.GetCmekSettingsRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for get_cmek_settings

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_get_cmek_settings(self, response: logging_config.CmekSettings) -> logging_config.CmekSettings:
        """Post-rpc interceptor for get_cmek_settings

        DEPRECATED. Please use the `post_get_cmek_settings_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_get_cmek_settings` interceptor runs
        before the `post_get_cmek_settings_with_metadata` interceptor.
        """
        return response

    def post_get_cmek_settings_with_metadata(self, response: logging_config.CmekSettings, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.CmekSettings, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for get_cmek_settings

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_get_cmek_settings_with_metadata`
        interceptor in new development instead of the `post_get_cmek_settings` interceptor.
        When both interceptors are used, this `post_get_cmek_settings_with_metadata` interceptor runs after the
        `post_get_cmek_settings` interceptor. The (possibly modified) response returned by
        `post_get_cmek_settings` will be passed to
        `post_get_cmek_settings_with_metadata`.
        """
        return response, metadata

    def pre_get_exclusion(self, request: logging_config.GetExclusionRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.GetExclusionRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for get_exclusion

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_get_exclusion(self, response: logging_config.LogExclusion) -> logging_config.LogExclusion:
        """Post-rpc interceptor for get_exclusion

        DEPRECATED. Please use the `post_get_exclusion_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_get_exclusion` interceptor runs
        before the `post_get_exclusion_with_metadata` interceptor.
        """
        return response

    def post_get_exclusion_with_metadata(self, response: logging_config.LogExclusion, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogExclusion, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for get_exclusion

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_get_exclusion_with_metadata`
        interceptor in new development instead of the `post_get_exclusion` interceptor.
        When both interceptors are used, this `post_get_exclusion_with_metadata` interceptor runs after the
        `post_get_exclusion` interceptor. The (possibly modified) response returned by
        `post_get_exclusion` will be passed to
        `post_get_exclusion_with_metadata`.
        """
        return response, metadata

    def pre_get_link(self, request: logging_config.GetLinkRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.GetLinkRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for get_link

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_get_link(self, response: logging_config.Link) -> logging_config.Link:
        """Post-rpc interceptor for get_link

        DEPRECATED. Please use the `post_get_link_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_get_link` interceptor runs
        before the `post_get_link_with_metadata` interceptor.
        """
        return response

    def post_get_link_with_metadata(self, response: logging_config.Link, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.Link, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for get_link

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_get_link_with_metadata`
        interceptor in new development instead of the `post_get_link` interceptor.
        When both interceptors are used, this `post_get_link_with_metadata` interceptor runs after the
        `post_get_link` interceptor. The (possibly modified) response returned by
        `post_get_link` will be passed to
        `post_get_link_with_metadata`.
        """
        return response, metadata

    def pre_get_log_scope(self, request: logging_config.GetLogScopeRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.GetLogScopeRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for get_log_scope

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_get_log_scope(self, response: logging_config.LogScope) -> logging_config.LogScope:
        """Post-rpc interceptor for get_log_scope

        DEPRECATED. Please use the `post_get_log_scope_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_get_log_scope` interceptor runs
        before the `post_get_log_scope_with_metadata` interceptor.
        """
        return response

    def post_get_log_scope_with_metadata(self, response: logging_config.LogScope, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogScope, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for get_log_scope

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_get_log_scope_with_metadata`
        interceptor in new development instead of the `post_get_log_scope` interceptor.
        When both interceptors are used, this `post_get_log_scope_with_metadata` interceptor runs after the
        `post_get_log_scope` interceptor. The (possibly modified) response returned by
        `post_get_log_scope` will be passed to
        `post_get_log_scope_with_metadata`.
        """
        return response, metadata

    def pre_get_saved_query(self, request: logging_config.GetSavedQueryRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.GetSavedQueryRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for get_saved_query

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_get_saved_query(self, response: logging_config.SavedQuery) -> logging_config.SavedQuery:
        """Post-rpc interceptor for get_saved_query

        DEPRECATED. Please use the `post_get_saved_query_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_get_saved_query` interceptor runs
        before the `post_get_saved_query_with_metadata` interceptor.
        """
        return response

    def post_get_saved_query_with_metadata(self, response: logging_config.SavedQuery, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.SavedQuery, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for get_saved_query

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_get_saved_query_with_metadata`
        interceptor in new development instead of the `post_get_saved_query` interceptor.
        When both interceptors are used, this `post_get_saved_query_with_metadata` interceptor runs after the
        `post_get_saved_query` interceptor. The (possibly modified) response returned by
        `post_get_saved_query` will be passed to
        `post_get_saved_query_with_metadata`.
        """
        return response, metadata

    def pre_get_settings(self, request: logging_config.GetSettingsRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.GetSettingsRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for get_settings

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_get_settings(self, response: logging_config.Settings) -> logging_config.Settings:
        """Post-rpc interceptor for get_settings

        DEPRECATED. Please use the `post_get_settings_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_get_settings` interceptor runs
        before the `post_get_settings_with_metadata` interceptor.
        """
        return response

    def post_get_settings_with_metadata(self, response: logging_config.Settings, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.Settings, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for get_settings

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_get_settings_with_metadata`
        interceptor in new development instead of the `post_get_settings` interceptor.
        When both interceptors are used, this `post_get_settings_with_metadata` interceptor runs after the
        `post_get_settings` interceptor. The (possibly modified) response returned by
        `post_get_settings` will be passed to
        `post_get_settings_with_metadata`.
        """
        return response, metadata

    def pre_get_sink(self, request: logging_config.GetSinkRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.GetSinkRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for get_sink

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_get_sink(self, response: logging_config.LogSink) -> logging_config.LogSink:
        """Post-rpc interceptor for get_sink

        DEPRECATED. Please use the `post_get_sink_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_get_sink` interceptor runs
        before the `post_get_sink_with_metadata` interceptor.
        """
        return response

    def post_get_sink_with_metadata(self, response: logging_config.LogSink, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogSink, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for get_sink

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_get_sink_with_metadata`
        interceptor in new development instead of the `post_get_sink` interceptor.
        When both interceptors are used, this `post_get_sink_with_metadata` interceptor runs after the
        `post_get_sink` interceptor. The (possibly modified) response returned by
        `post_get_sink` will be passed to
        `post_get_sink_with_metadata`.
        """
        return response, metadata

    def pre_get_view(self, request: logging_config.GetViewRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.GetViewRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for get_view

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_get_view(self, response: logging_config.LogView) -> logging_config.LogView:
        """Post-rpc interceptor for get_view

        DEPRECATED. Please use the `post_get_view_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_get_view` interceptor runs
        before the `post_get_view_with_metadata` interceptor.
        """
        return response

    def post_get_view_with_metadata(self, response: logging_config.LogView, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogView, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for get_view

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_get_view_with_metadata`
        interceptor in new development instead of the `post_get_view` interceptor.
        When both interceptors are used, this `post_get_view_with_metadata` interceptor runs after the
        `post_get_view` interceptor. The (possibly modified) response returned by
        `post_get_view` will be passed to
        `post_get_view_with_metadata`.
        """
        return response, metadata

    def pre_list_buckets(self, request: logging_config.ListBucketsRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListBucketsRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_buckets

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_list_buckets(self, response: logging_config.ListBucketsResponse) -> logging_config.ListBucketsResponse:
        """Post-rpc interceptor for list_buckets

        DEPRECATED. Please use the `post_list_buckets_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_list_buckets` interceptor runs
        before the `post_list_buckets_with_metadata` interceptor.
        """
        return response

    def post_list_buckets_with_metadata(self, response: logging_config.ListBucketsResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListBucketsResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_buckets

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_buckets_with_metadata`
        interceptor in new development instead of the `post_list_buckets` interceptor.
        When both interceptors are used, this `post_list_buckets_with_metadata` interceptor runs after the
        `post_list_buckets` interceptor. The (possibly modified) response returned by
        `post_list_buckets` will be passed to
        `post_list_buckets_with_metadata`.
        """
        return response, metadata

    def pre_list_exclusions(self, request: logging_config.ListExclusionsRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListExclusionsRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_exclusions

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_list_exclusions(self, response: logging_config.ListExclusionsResponse) -> logging_config.ListExclusionsResponse:
        """Post-rpc interceptor for list_exclusions

        DEPRECATED. Please use the `post_list_exclusions_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_list_exclusions` interceptor runs
        before the `post_list_exclusions_with_metadata` interceptor.
        """
        return response

    def post_list_exclusions_with_metadata(self, response: logging_config.ListExclusionsResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListExclusionsResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_exclusions

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_exclusions_with_metadata`
        interceptor in new development instead of the `post_list_exclusions` interceptor.
        When both interceptors are used, this `post_list_exclusions_with_metadata` interceptor runs after the
        `post_list_exclusions` interceptor. The (possibly modified) response returned by
        `post_list_exclusions` will be passed to
        `post_list_exclusions_with_metadata`.
        """
        return response, metadata

    def pre_list_links(self, request: logging_config.ListLinksRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListLinksRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_links

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_list_links(self, response: logging_config.ListLinksResponse) -> logging_config.ListLinksResponse:
        """Post-rpc interceptor for list_links

        DEPRECATED. Please use the `post_list_links_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_list_links` interceptor runs
        before the `post_list_links_with_metadata` interceptor.
        """
        return response

    def post_list_links_with_metadata(self, response: logging_config.ListLinksResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListLinksResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_links

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_links_with_metadata`
        interceptor in new development instead of the `post_list_links` interceptor.
        When both interceptors are used, this `post_list_links_with_metadata` interceptor runs after the
        `post_list_links` interceptor. The (possibly modified) response returned by
        `post_list_links` will be passed to
        `post_list_links_with_metadata`.
        """
        return response, metadata

    def pre_list_log_scopes(self, request: logging_config.ListLogScopesRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListLogScopesRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_log_scopes

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_list_log_scopes(self, response: logging_config.ListLogScopesResponse) -> logging_config.ListLogScopesResponse:
        """Post-rpc interceptor for list_log_scopes

        DEPRECATED. Please use the `post_list_log_scopes_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_list_log_scopes` interceptor runs
        before the `post_list_log_scopes_with_metadata` interceptor.
        """
        return response

    def post_list_log_scopes_with_metadata(self, response: logging_config.ListLogScopesResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListLogScopesResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_log_scopes

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_log_scopes_with_metadata`
        interceptor in new development instead of the `post_list_log_scopes` interceptor.
        When both interceptors are used, this `post_list_log_scopes_with_metadata` interceptor runs after the
        `post_list_log_scopes` interceptor. The (possibly modified) response returned by
        `post_list_log_scopes` will be passed to
        `post_list_log_scopes_with_metadata`.
        """
        return response, metadata

    def pre_list_recent_queries(self, request: logging_config.ListRecentQueriesRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListRecentQueriesRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_recent_queries

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_list_recent_queries(self, response: logging_config.ListRecentQueriesResponse) -> logging_config.ListRecentQueriesResponse:
        """Post-rpc interceptor for list_recent_queries

        DEPRECATED. Please use the `post_list_recent_queries_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_list_recent_queries` interceptor runs
        before the `post_list_recent_queries_with_metadata` interceptor.
        """
        return response

    def post_list_recent_queries_with_metadata(self, response: logging_config.ListRecentQueriesResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListRecentQueriesResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_recent_queries

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_recent_queries_with_metadata`
        interceptor in new development instead of the `post_list_recent_queries` interceptor.
        When both interceptors are used, this `post_list_recent_queries_with_metadata` interceptor runs after the
        `post_list_recent_queries` interceptor. The (possibly modified) response returned by
        `post_list_recent_queries` will be passed to
        `post_list_recent_queries_with_metadata`.
        """
        return response, metadata

    def pre_list_saved_queries(self, request: logging_config.ListSavedQueriesRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListSavedQueriesRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_saved_queries

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_list_saved_queries(self, response: logging_config.ListSavedQueriesResponse) -> logging_config.ListSavedQueriesResponse:
        """Post-rpc interceptor for list_saved_queries

        DEPRECATED. Please use the `post_list_saved_queries_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_list_saved_queries` interceptor runs
        before the `post_list_saved_queries_with_metadata` interceptor.
        """
        return response

    def post_list_saved_queries_with_metadata(self, response: logging_config.ListSavedQueriesResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListSavedQueriesResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_saved_queries

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_saved_queries_with_metadata`
        interceptor in new development instead of the `post_list_saved_queries` interceptor.
        When both interceptors are used, this `post_list_saved_queries_with_metadata` interceptor runs after the
        `post_list_saved_queries` interceptor. The (possibly modified) response returned by
        `post_list_saved_queries` will be passed to
        `post_list_saved_queries_with_metadata`.
        """
        return response, metadata

    def pre_list_sinks(self, request: logging_config.ListSinksRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListSinksRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_sinks

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_list_sinks(self, response: logging_config.ListSinksResponse) -> logging_config.ListSinksResponse:
        """Post-rpc interceptor for list_sinks

        DEPRECATED. Please use the `post_list_sinks_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_list_sinks` interceptor runs
        before the `post_list_sinks_with_metadata` interceptor.
        """
        return response

    def post_list_sinks_with_metadata(self, response: logging_config.ListSinksResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListSinksResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_sinks

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_sinks_with_metadata`
        interceptor in new development instead of the `post_list_sinks` interceptor.
        When both interceptors are used, this `post_list_sinks_with_metadata` interceptor runs after the
        `post_list_sinks` interceptor. The (possibly modified) response returned by
        `post_list_sinks` will be passed to
        `post_list_sinks_with_metadata`.
        """
        return response, metadata

    def pre_list_views(self, request: logging_config.ListViewsRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListViewsRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for list_views

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_list_views(self, response: logging_config.ListViewsResponse) -> logging_config.ListViewsResponse:
        """Post-rpc interceptor for list_views

        DEPRECATED. Please use the `post_list_views_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_list_views` interceptor runs
        before the `post_list_views_with_metadata` interceptor.
        """
        return response

    def post_list_views_with_metadata(self, response: logging_config.ListViewsResponse, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.ListViewsResponse, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for list_views

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_list_views_with_metadata`
        interceptor in new development instead of the `post_list_views` interceptor.
        When both interceptors are used, this `post_list_views_with_metadata` interceptor runs after the
        `post_list_views` interceptor. The (possibly modified) response returned by
        `post_list_views` will be passed to
        `post_list_views_with_metadata`.
        """
        return response, metadata

    def pre_undelete_bucket(self, request: logging_config.UndeleteBucketRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.UndeleteBucketRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for undelete_bucket

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def pre_update_bucket(self, request: logging_config.UpdateBucketRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.UpdateBucketRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for update_bucket

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_update_bucket(self, response: logging_config.LogBucket) -> logging_config.LogBucket:
        """Post-rpc interceptor for update_bucket

        DEPRECATED. Please use the `post_update_bucket_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_update_bucket` interceptor runs
        before the `post_update_bucket_with_metadata` interceptor.
        """
        return response

    def post_update_bucket_with_metadata(self, response: logging_config.LogBucket, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogBucket, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for update_bucket

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_update_bucket_with_metadata`
        interceptor in new development instead of the `post_update_bucket` interceptor.
        When both interceptors are used, this `post_update_bucket_with_metadata` interceptor runs after the
        `post_update_bucket` interceptor. The (possibly modified) response returned by
        `post_update_bucket` will be passed to
        `post_update_bucket_with_metadata`.
        """
        return response, metadata

    def pre_update_bucket_async(self, request: logging_config.UpdateBucketRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.UpdateBucketRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for update_bucket_async

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_update_bucket_async(self, response: operations_pb2.Operation) -> operations_pb2.Operation:
        """Post-rpc interceptor for update_bucket_async

        DEPRECATED. Please use the `post_update_bucket_async_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_update_bucket_async` interceptor runs
        before the `post_update_bucket_async_with_metadata` interceptor.
        """
        return response

    def post_update_bucket_async_with_metadata(self, response: operations_pb2.Operation, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[operations_pb2.Operation, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for update_bucket_async

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_update_bucket_async_with_metadata`
        interceptor in new development instead of the `post_update_bucket_async` interceptor.
        When both interceptors are used, this `post_update_bucket_async_with_metadata` interceptor runs after the
        `post_update_bucket_async` interceptor. The (possibly modified) response returned by
        `post_update_bucket_async` will be passed to
        `post_update_bucket_async_with_metadata`.
        """
        return response, metadata

    def pre_update_cmek_settings(self, request: logging_config.UpdateCmekSettingsRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.UpdateCmekSettingsRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for update_cmek_settings

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_update_cmek_settings(self, response: logging_config.CmekSettings) -> logging_config.CmekSettings:
        """Post-rpc interceptor for update_cmek_settings

        DEPRECATED. Please use the `post_update_cmek_settings_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_update_cmek_settings` interceptor runs
        before the `post_update_cmek_settings_with_metadata` interceptor.
        """
        return response

    def post_update_cmek_settings_with_metadata(self, response: logging_config.CmekSettings, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.CmekSettings, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for update_cmek_settings

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_update_cmek_settings_with_metadata`
        interceptor in new development instead of the `post_update_cmek_settings` interceptor.
        When both interceptors are used, this `post_update_cmek_settings_with_metadata` interceptor runs after the
        `post_update_cmek_settings` interceptor. The (possibly modified) response returned by
        `post_update_cmek_settings` will be passed to
        `post_update_cmek_settings_with_metadata`.
        """
        return response, metadata

    def pre_update_exclusion(self, request: logging_config.UpdateExclusionRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.UpdateExclusionRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for update_exclusion

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_update_exclusion(self, response: logging_config.LogExclusion) -> logging_config.LogExclusion:
        """Post-rpc interceptor for update_exclusion

        DEPRECATED. Please use the `post_update_exclusion_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_update_exclusion` interceptor runs
        before the `post_update_exclusion_with_metadata` interceptor.
        """
        return response

    def post_update_exclusion_with_metadata(self, response: logging_config.LogExclusion, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogExclusion, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for update_exclusion

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_update_exclusion_with_metadata`
        interceptor in new development instead of the `post_update_exclusion` interceptor.
        When both interceptors are used, this `post_update_exclusion_with_metadata` interceptor runs after the
        `post_update_exclusion` interceptor. The (possibly modified) response returned by
        `post_update_exclusion` will be passed to
        `post_update_exclusion_with_metadata`.
        """
        return response, metadata

    def pre_update_log_scope(self, request: logging_config.UpdateLogScopeRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.UpdateLogScopeRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for update_log_scope

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_update_log_scope(self, response: logging_config.LogScope) -> logging_config.LogScope:
        """Post-rpc interceptor for update_log_scope

        DEPRECATED. Please use the `post_update_log_scope_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_update_log_scope` interceptor runs
        before the `post_update_log_scope_with_metadata` interceptor.
        """
        return response

    def post_update_log_scope_with_metadata(self, response: logging_config.LogScope, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogScope, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for update_log_scope

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_update_log_scope_with_metadata`
        interceptor in new development instead of the `post_update_log_scope` interceptor.
        When both interceptors are used, this `post_update_log_scope_with_metadata` interceptor runs after the
        `post_update_log_scope` interceptor. The (possibly modified) response returned by
        `post_update_log_scope` will be passed to
        `post_update_log_scope_with_metadata`.
        """
        return response, metadata

    def pre_update_saved_query(self, request: logging_config.UpdateSavedQueryRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.UpdateSavedQueryRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for update_saved_query

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_update_saved_query(self, response: logging_config.SavedQuery) -> logging_config.SavedQuery:
        """Post-rpc interceptor for update_saved_query

        DEPRECATED. Please use the `post_update_saved_query_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_update_saved_query` interceptor runs
        before the `post_update_saved_query_with_metadata` interceptor.
        """
        return response

    def post_update_saved_query_with_metadata(self, response: logging_config.SavedQuery, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.SavedQuery, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for update_saved_query

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_update_saved_query_with_metadata`
        interceptor in new development instead of the `post_update_saved_query` interceptor.
        When both interceptors are used, this `post_update_saved_query_with_metadata` interceptor runs after the
        `post_update_saved_query` interceptor. The (possibly modified) response returned by
        `post_update_saved_query` will be passed to
        `post_update_saved_query_with_metadata`.
        """
        return response, metadata

    def pre_update_settings(self, request: logging_config.UpdateSettingsRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.UpdateSettingsRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for update_settings

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_update_settings(self, response: logging_config.Settings) -> logging_config.Settings:
        """Post-rpc interceptor for update_settings

        DEPRECATED. Please use the `post_update_settings_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_update_settings` interceptor runs
        before the `post_update_settings_with_metadata` interceptor.
        """
        return response

    def post_update_settings_with_metadata(self, response: logging_config.Settings, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.Settings, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for update_settings

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_update_settings_with_metadata`
        interceptor in new development instead of the `post_update_settings` interceptor.
        When both interceptors are used, this `post_update_settings_with_metadata` interceptor runs after the
        `post_update_settings` interceptor. The (possibly modified) response returned by
        `post_update_settings` will be passed to
        `post_update_settings_with_metadata`.
        """
        return response, metadata

    def pre_update_sink(self, request: logging_config.UpdateSinkRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.UpdateSinkRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for update_sink

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_update_sink(self, response: logging_config.LogSink) -> logging_config.LogSink:
        """Post-rpc interceptor for update_sink

        DEPRECATED. Please use the `post_update_sink_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_update_sink` interceptor runs
        before the `post_update_sink_with_metadata` interceptor.
        """
        return response

    def post_update_sink_with_metadata(self, response: logging_config.LogSink, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogSink, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for update_sink

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_update_sink_with_metadata`
        interceptor in new development instead of the `post_update_sink` interceptor.
        When both interceptors are used, this `post_update_sink_with_metadata` interceptor runs after the
        `post_update_sink` interceptor. The (possibly modified) response returned by
        `post_update_sink` will be passed to
        `post_update_sink_with_metadata`.
        """
        return response, metadata

    def pre_update_view(self, request: logging_config.UpdateViewRequest, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.UpdateViewRequest, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Pre-rpc interceptor for update_view

        Override in a subclass to manipulate the request or metadata
        before they are sent to the ConfigServiceV2 server.
        """
        return request, metadata

    def post_update_view(self, response: logging_config.LogView) -> logging_config.LogView:
        """Post-rpc interceptor for update_view

        DEPRECATED. Please use the `post_update_view_with_metadata`
        interceptor instead.

        Override in a subclass to read or manipulate the response
        after it is returned by the ConfigServiceV2 server but before
        it is returned to user code. This `post_update_view` interceptor runs
        before the `post_update_view_with_metadata` interceptor.
        """
        return response

    def post_update_view_with_metadata(self, response: logging_config.LogView, metadata: Sequence[Tuple[str, Union[str, bytes]]]) -> Tuple[logging_config.LogView, Sequence[Tuple[str, Union[str, bytes]]]]:
        """Post-rpc interceptor for update_view

        Override in a subclass to read or manipulate the response or metadata after it
        is returned by the ConfigServiceV2 server but before it is returned to user code.

        We recommend only using this `post_update_view_with_metadata`
        interceptor in new development instead of the `post_update_view` interceptor.
        When both interceptors are used, this `post_update_view_with_metadata` interceptor runs after the
        `post_update_view` interceptor. The (possibly modified) response returned by
        `post_update_view` will be passed to
        `post_update_view_with_metadata`.
        """
        return response, metadata


@dataclasses.dataclass
class ConfigServiceV2RestStub:
    _session: AuthorizedSession
    _host: str
    _interceptor: ConfigServiceV2RestInterceptor


class ConfigServiceV2RestTransport(_BaseConfigServiceV2RestTransport):
    """REST backend synchronous transport for ConfigServiceV2.

    Service for configuring sinks used to route log entries.

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
            interceptor: Optional[ConfigServiceV2RestInterceptor] = None,
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
        self._operations_client: Optional[operations_v1.AbstractOperationsClient] = None
        if client_cert_source_for_mtls:
            self._session.configure_mtls_channel(client_cert_source_for_mtls)
        self._interceptor = interceptor or ConfigServiceV2RestInterceptor()
        self._prep_wrapped_messages(client_info)

    @property
    def operations_client(self) -> operations_v1.AbstractOperationsClient:
        """Create the client designed to process long-running operations.

        This property caches on the instance; repeated calls return the same
        client.
        """
        # Only create a new client if we do not already have one.
        if self._operations_client is None:
            http_options: Dict[str, List[Dict[str, str]]] = {
            }

            rest_transport = operations_v1.OperationsRestTransport(
                    host=self._host,
                    # use the credentials which are saved
                    credentials=self._credentials,
                    scopes=self._scopes,
                    http_options=http_options,
                    path_prefix="v2")

            self._operations_client = operations_v1.AbstractOperationsClient(transport=rest_transport)

        # Return the client from cache.
        return self._operations_client

    class _CopyLogEntries(_BaseConfigServiceV2RestTransport._BaseCopyLogEntries, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.CopyLogEntries")

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
                request: logging_config.CopyLogEntriesRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> operations_pb2.Operation:
            r"""Call the copy log entries method over HTTP.

            Args:
                request (~.logging_config.CopyLogEntriesRequest):
                    The request object. The parameters to CopyLogEntries.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.operations_pb2.Operation:
                    This resource represents a
                long-running operation that is the
                result of a network API call.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseCopyLogEntries._get_http_options()

            request, metadata = self._interceptor.pre_copy_log_entries(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseCopyLogEntries._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseCopyLogEntries._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseCopyLogEntries._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.CopyLogEntries",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CopyLogEntries",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._CopyLogEntries._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = operations_pb2.Operation()
            json_format.Parse(response.content, resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_copy_log_entries(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_copy_log_entries_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = json_format.MessageToJson(resp)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.copy_log_entries",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CopyLogEntries",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _CreateBucket(_BaseConfigServiceV2RestTransport._BaseCreateBucket, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.CreateBucket")

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
                request: logging_config.CreateBucketRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogBucket:
            r"""Call the create bucket method over HTTP.

            Args:
                request (~.logging_config.CreateBucketRequest):
                    The request object. The parameters to ``CreateBucket``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogBucket:
                    Describes a repository in which log
                entries are stored.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseCreateBucket._get_http_options()

            request, metadata = self._interceptor.pre_create_bucket(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseCreateBucket._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseCreateBucket._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseCreateBucket._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.CreateBucket",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateBucket",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._CreateBucket._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogBucket()
            pb_resp = logging_config.LogBucket.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_create_bucket(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_create_bucket_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogBucket.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.create_bucket",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateBucket",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _CreateBucketAsync(_BaseConfigServiceV2RestTransport._BaseCreateBucketAsync, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.CreateBucketAsync")

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
                request: logging_config.CreateBucketRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> operations_pb2.Operation:
            r"""Call the create bucket async method over HTTP.

            Args:
                request (~.logging_config.CreateBucketRequest):
                    The request object. The parameters to ``CreateBucket``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.operations_pb2.Operation:
                    This resource represents a
                long-running operation that is the
                result of a network API call.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseCreateBucketAsync._get_http_options()

            request, metadata = self._interceptor.pre_create_bucket_async(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseCreateBucketAsync._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseCreateBucketAsync._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseCreateBucketAsync._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.CreateBucketAsync",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateBucketAsync",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._CreateBucketAsync._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = operations_pb2.Operation()
            json_format.Parse(response.content, resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_create_bucket_async(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_create_bucket_async_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = json_format.MessageToJson(resp)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.create_bucket_async",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateBucketAsync",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _CreateExclusion(_BaseConfigServiceV2RestTransport._BaseCreateExclusion, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.CreateExclusion")

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
                request: logging_config.CreateExclusionRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogExclusion:
            r"""Call the create exclusion method over HTTP.

            Args:
                request (~.logging_config.CreateExclusionRequest):
                    The request object. The parameters to ``CreateExclusion``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogExclusion:
                    Specifies a set of log entries that are filtered out by
                a sink. If your Google Cloud resource receives a large
                volume of log entries, you can use exclusions to reduce
                your chargeable logs. Note that exclusions on
                organization-level and folder-level sinks don't apply to
                child resources. Note also that you cannot modify the
                \_Required sink or exclude logs from it.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseCreateExclusion._get_http_options()

            request, metadata = self._interceptor.pre_create_exclusion(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseCreateExclusion._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseCreateExclusion._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseCreateExclusion._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.CreateExclusion",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateExclusion",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._CreateExclusion._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogExclusion()
            pb_resp = logging_config.LogExclusion.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_create_exclusion(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_create_exclusion_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogExclusion.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.create_exclusion",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateExclusion",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _CreateLink(_BaseConfigServiceV2RestTransport._BaseCreateLink, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.CreateLink")

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
                request: logging_config.CreateLinkRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> operations_pb2.Operation:
            r"""Call the create link method over HTTP.

            Args:
                request (~.logging_config.CreateLinkRequest):
                    The request object. The parameters to CreateLink.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.operations_pb2.Operation:
                    This resource represents a
                long-running operation that is the
                result of a network API call.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseCreateLink._get_http_options()

            request, metadata = self._interceptor.pre_create_link(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseCreateLink._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseCreateLink._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseCreateLink._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.CreateLink",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateLink",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._CreateLink._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = operations_pb2.Operation()
            json_format.Parse(response.content, resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_create_link(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_create_link_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = json_format.MessageToJson(resp)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.create_link",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateLink",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _CreateLogScope(_BaseConfigServiceV2RestTransport._BaseCreateLogScope, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.CreateLogScope")

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
                request: logging_config.CreateLogScopeRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogScope:
            r"""Call the create log scope method over HTTP.

            Args:
                request (~.logging_config.CreateLogScopeRequest):
                    The request object. The parameters to ``CreateLogScope``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogScope:
                    Describes a group of resources to
                read log entries from.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseCreateLogScope._get_http_options()

            request, metadata = self._interceptor.pre_create_log_scope(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseCreateLogScope._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseCreateLogScope._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseCreateLogScope._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.CreateLogScope",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateLogScope",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._CreateLogScope._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogScope()
            pb_resp = logging_config.LogScope.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_create_log_scope(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_create_log_scope_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogScope.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.create_log_scope",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateLogScope",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _CreateSavedQuery(_BaseConfigServiceV2RestTransport._BaseCreateSavedQuery, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.CreateSavedQuery")

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
                request: logging_config.CreateSavedQueryRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.SavedQuery:
            r"""Call the create saved query method over HTTP.

            Args:
                request (~.logging_config.CreateSavedQueryRequest):
                    The request object. The parameters to 'CreateSavedQuery'.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.SavedQuery:
                    Describes a query that has been saved
                by a user.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseCreateSavedQuery._get_http_options()

            request, metadata = self._interceptor.pre_create_saved_query(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseCreateSavedQuery._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseCreateSavedQuery._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseCreateSavedQuery._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.CreateSavedQuery",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateSavedQuery",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._CreateSavedQuery._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.SavedQuery()
            pb_resp = logging_config.SavedQuery.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_create_saved_query(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_create_saved_query_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.SavedQuery.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.create_saved_query",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateSavedQuery",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _CreateSink(_BaseConfigServiceV2RestTransport._BaseCreateSink, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.CreateSink")

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
                request: logging_config.CreateSinkRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogSink:
            r"""Call the create sink method over HTTP.

            Args:
                request (~.logging_config.CreateSinkRequest):
                    The request object. The parameters to ``CreateSink``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogSink:
                    Describes a sink used to export log entries to one of
                the following destinations:

                - a Cloud Logging log bucket,
                - a Cloud Storage bucket,
                - a BigQuery dataset,
                - a Pub/Sub topic,
                - a Cloud project.

                A logs filter controls which log entries are exported.
                The sink must be created within a project, organization,
                billing account, or folder.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseCreateSink._get_http_options()

            request, metadata = self._interceptor.pre_create_sink(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseCreateSink._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseCreateSink._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseCreateSink._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.CreateSink",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateSink",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._CreateSink._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogSink()
            pb_resp = logging_config.LogSink.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_create_sink(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_create_sink_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogSink.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.create_sink",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateSink",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _CreateView(_BaseConfigServiceV2RestTransport._BaseCreateView, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.CreateView")

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
                request: logging_config.CreateViewRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogView:
            r"""Call the create view method over HTTP.

            Args:
                request (~.logging_config.CreateViewRequest):
                    The request object. The parameters to ``CreateView``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogView:
                    Describes a view over log entries in
                a bucket.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseCreateView._get_http_options()

            request, metadata = self._interceptor.pre_create_view(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseCreateView._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseCreateView._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseCreateView._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.CreateView",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateView",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._CreateView._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogView()
            pb_resp = logging_config.LogView.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_create_view(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_create_view_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogView.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.create_view",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "CreateView",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _DeleteBucket(_BaseConfigServiceV2RestTransport._BaseDeleteBucket, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.DeleteBucket")

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
                request: logging_config.DeleteBucketRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ):
            r"""Call the delete bucket method over HTTP.

            Args:
                request (~.logging_config.DeleteBucketRequest):
                    The request object. The parameters to ``DeleteBucket``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseDeleteBucket._get_http_options()

            request, metadata = self._interceptor.pre_delete_bucket(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseDeleteBucket._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseDeleteBucket._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.DeleteBucket",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "DeleteBucket",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._DeleteBucket._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

    class _DeleteExclusion(_BaseConfigServiceV2RestTransport._BaseDeleteExclusion, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.DeleteExclusion")

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
                request: logging_config.DeleteExclusionRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ):
            r"""Call the delete exclusion method over HTTP.

            Args:
                request (~.logging_config.DeleteExclusionRequest):
                    The request object. The parameters to ``DeleteExclusion``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseDeleteExclusion._get_http_options()

            request, metadata = self._interceptor.pre_delete_exclusion(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseDeleteExclusion._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseDeleteExclusion._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.DeleteExclusion",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "DeleteExclusion",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._DeleteExclusion._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

    class _DeleteLink(_BaseConfigServiceV2RestTransport._BaseDeleteLink, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.DeleteLink")

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
                request: logging_config.DeleteLinkRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> operations_pb2.Operation:
            r"""Call the delete link method over HTTP.

            Args:
                request (~.logging_config.DeleteLinkRequest):
                    The request object. The parameters to DeleteLink.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.operations_pb2.Operation:
                    This resource represents a
                long-running operation that is the
                result of a network API call.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseDeleteLink._get_http_options()

            request, metadata = self._interceptor.pre_delete_link(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseDeleteLink._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseDeleteLink._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.DeleteLink",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "DeleteLink",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._DeleteLink._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = operations_pb2.Operation()
            json_format.Parse(response.content, resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_delete_link(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_delete_link_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = json_format.MessageToJson(resp)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.delete_link",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "DeleteLink",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _DeleteLogScope(_BaseConfigServiceV2RestTransport._BaseDeleteLogScope, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.DeleteLogScope")

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
                request: logging_config.DeleteLogScopeRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ):
            r"""Call the delete log scope method over HTTP.

            Args:
                request (~.logging_config.DeleteLogScopeRequest):
                    The request object. The parameters to ``DeleteLogScope``. The ``_Default``
                log scope cannot be deleted.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseDeleteLogScope._get_http_options()

            request, metadata = self._interceptor.pre_delete_log_scope(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseDeleteLogScope._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseDeleteLogScope._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.DeleteLogScope",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "DeleteLogScope",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._DeleteLogScope._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

    class _DeleteSavedQuery(_BaseConfigServiceV2RestTransport._BaseDeleteSavedQuery, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.DeleteSavedQuery")

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
                request: logging_config.DeleteSavedQueryRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ):
            r"""Call the delete saved query method over HTTP.

            Args:
                request (~.logging_config.DeleteSavedQueryRequest):
                    The request object. The parameters to 'DeleteSavedQuery'.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseDeleteSavedQuery._get_http_options()

            request, metadata = self._interceptor.pre_delete_saved_query(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseDeleteSavedQuery._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseDeleteSavedQuery._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.DeleteSavedQuery",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "DeleteSavedQuery",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._DeleteSavedQuery._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

    class _DeleteSink(_BaseConfigServiceV2RestTransport._BaseDeleteSink, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.DeleteSink")

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
                request: logging_config.DeleteSinkRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ):
            r"""Call the delete sink method over HTTP.

            Args:
                request (~.logging_config.DeleteSinkRequest):
                    The request object. The parameters to ``DeleteSink``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseDeleteSink._get_http_options()

            request, metadata = self._interceptor.pre_delete_sink(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseDeleteSink._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseDeleteSink._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.DeleteSink",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "DeleteSink",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._DeleteSink._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

    class _DeleteView(_BaseConfigServiceV2RestTransport._BaseDeleteView, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.DeleteView")

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
                request: logging_config.DeleteViewRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ):
            r"""Call the delete view method over HTTP.

            Args:
                request (~.logging_config.DeleteViewRequest):
                    The request object. The parameters to ``DeleteView``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseDeleteView._get_http_options()

            request, metadata = self._interceptor.pre_delete_view(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseDeleteView._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseDeleteView._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.DeleteView",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "DeleteView",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._DeleteView._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

    class _GetBucket(_BaseConfigServiceV2RestTransport._BaseGetBucket, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.GetBucket")

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
                request: logging_config.GetBucketRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogBucket:
            r"""Call the get bucket method over HTTP.

            Args:
                request (~.logging_config.GetBucketRequest):
                    The request object. The parameters to ``GetBucket``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogBucket:
                    Describes a repository in which log
                entries are stored.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseGetBucket._get_http_options()

            request, metadata = self._interceptor.pre_get_bucket(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseGetBucket._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseGetBucket._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.GetBucket",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetBucket",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._GetBucket._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogBucket()
            pb_resp = logging_config.LogBucket.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_get_bucket(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_get_bucket_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogBucket.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.get_bucket",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetBucket",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _GetCmekSettings(_BaseConfigServiceV2RestTransport._BaseGetCmekSettings, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.GetCmekSettings")

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
                request: logging_config.GetCmekSettingsRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.CmekSettings:
            r"""Call the get cmek settings method over HTTP.

            Args:
                request (~.logging_config.GetCmekSettingsRequest):
                    The request object. The parameters to
                [GetCmekSettings][google.logging.v2.ConfigServiceV2.GetCmekSettings].

                See `Configure CMEK for Cloud
                Logging <https://docs.cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.CmekSettings:
                    Describes the customer-managed encryption key (CMEK)
                settings associated with a project, folder,
                organization, billing account, or flexible resource.

                Note: CMEK for the Log Router can currently only be
                configured for Google Cloud organizations. Once
                configured, it applies to all projects and folders in
                the Google Cloud organization.

                See `Configure CMEK for Cloud
                Logging <https://docs.cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseGetCmekSettings._get_http_options()

            request, metadata = self._interceptor.pre_get_cmek_settings(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseGetCmekSettings._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseGetCmekSettings._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.GetCmekSettings",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetCmekSettings",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._GetCmekSettings._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.CmekSettings()
            pb_resp = logging_config.CmekSettings.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_get_cmek_settings(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_get_cmek_settings_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.CmekSettings.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.get_cmek_settings",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetCmekSettings",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _GetExclusion(_BaseConfigServiceV2RestTransport._BaseGetExclusion, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.GetExclusion")

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
                request: logging_config.GetExclusionRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogExclusion:
            r"""Call the get exclusion method over HTTP.

            Args:
                request (~.logging_config.GetExclusionRequest):
                    The request object. The parameters to ``GetExclusion``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogExclusion:
                    Specifies a set of log entries that are filtered out by
                a sink. If your Google Cloud resource receives a large
                volume of log entries, you can use exclusions to reduce
                your chargeable logs. Note that exclusions on
                organization-level and folder-level sinks don't apply to
                child resources. Note also that you cannot modify the
                \_Required sink or exclude logs from it.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseGetExclusion._get_http_options()

            request, metadata = self._interceptor.pre_get_exclusion(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseGetExclusion._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseGetExclusion._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.GetExclusion",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetExclusion",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._GetExclusion._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogExclusion()
            pb_resp = logging_config.LogExclusion.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_get_exclusion(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_get_exclusion_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogExclusion.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.get_exclusion",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetExclusion",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _GetLink(_BaseConfigServiceV2RestTransport._BaseGetLink, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.GetLink")

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
                request: logging_config.GetLinkRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.Link:
            r"""Call the get link method over HTTP.

            Args:
                request (~.logging_config.GetLinkRequest):
                    The request object. The parameters to GetLink.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.Link:
                    Describes a link connected to an
                analytics enabled bucket.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseGetLink._get_http_options()

            request, metadata = self._interceptor.pre_get_link(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseGetLink._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseGetLink._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.GetLink",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetLink",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._GetLink._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.Link()
            pb_resp = logging_config.Link.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_get_link(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_get_link_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.Link.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.get_link",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetLink",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _GetLogScope(_BaseConfigServiceV2RestTransport._BaseGetLogScope, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.GetLogScope")

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
                request: logging_config.GetLogScopeRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogScope:
            r"""Call the get log scope method over HTTP.

            Args:
                request (~.logging_config.GetLogScopeRequest):
                    The request object. The parameters to ``GetLogScope``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogScope:
                    Describes a group of resources to
                read log entries from.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseGetLogScope._get_http_options()

            request, metadata = self._interceptor.pre_get_log_scope(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseGetLogScope._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseGetLogScope._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.GetLogScope",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetLogScope",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._GetLogScope._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogScope()
            pb_resp = logging_config.LogScope.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_get_log_scope(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_get_log_scope_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogScope.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.get_log_scope",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetLogScope",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _GetSavedQuery(_BaseConfigServiceV2RestTransport._BaseGetSavedQuery, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.GetSavedQuery")

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
                request: logging_config.GetSavedQueryRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.SavedQuery:
            r"""Call the get saved query method over HTTP.

            Args:
                request (~.logging_config.GetSavedQueryRequest):
                    The request object. The parameters to 'GetSavedQuery'
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.SavedQuery:
                    Describes a query that has been saved
                by a user.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseGetSavedQuery._get_http_options()

            request, metadata = self._interceptor.pre_get_saved_query(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseGetSavedQuery._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseGetSavedQuery._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.GetSavedQuery",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetSavedQuery",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._GetSavedQuery._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.SavedQuery()
            pb_resp = logging_config.SavedQuery.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_get_saved_query(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_get_saved_query_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.SavedQuery.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.get_saved_query",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetSavedQuery",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _GetSettings(_BaseConfigServiceV2RestTransport._BaseGetSettings, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.GetSettings")

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
                request: logging_config.GetSettingsRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.Settings:
            r"""Call the get settings method over HTTP.

            Args:
                request (~.logging_config.GetSettingsRequest):
                    The request object. The parameters to
                [GetSettings][google.logging.v2.ConfigServiceV2.GetSettings].

                See [View default resource settings for Logging]
                (https://docs.cloud.google.com/logging/docs/default-settings#view-org-settings)
                for more information.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.Settings:
                    Describes the settings associated
                with a project, folder, organization, or
                billing account.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseGetSettings._get_http_options()

            request, metadata = self._interceptor.pre_get_settings(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseGetSettings._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseGetSettings._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.GetSettings",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetSettings",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._GetSettings._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.Settings()
            pb_resp = logging_config.Settings.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_get_settings(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_get_settings_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.Settings.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.get_settings",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetSettings",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _GetSink(_BaseConfigServiceV2RestTransport._BaseGetSink, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.GetSink")

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
                request: logging_config.GetSinkRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogSink:
            r"""Call the get sink method over HTTP.

            Args:
                request (~.logging_config.GetSinkRequest):
                    The request object. The parameters to ``GetSink``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogSink:
                    Describes a sink used to export log entries to one of
                the following destinations:

                - a Cloud Logging log bucket,
                - a Cloud Storage bucket,
                - a BigQuery dataset,
                - a Pub/Sub topic,
                - a Cloud project.

                A logs filter controls which log entries are exported.
                The sink must be created within a project, organization,
                billing account, or folder.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseGetSink._get_http_options()

            request, metadata = self._interceptor.pre_get_sink(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseGetSink._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseGetSink._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.GetSink",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetSink",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._GetSink._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogSink()
            pb_resp = logging_config.LogSink.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_get_sink(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_get_sink_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogSink.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.get_sink",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetSink",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _GetView(_BaseConfigServiceV2RestTransport._BaseGetView, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.GetView")

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
                request: logging_config.GetViewRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogView:
            r"""Call the get view method over HTTP.

            Args:
                request (~.logging_config.GetViewRequest):
                    The request object. The parameters to ``GetView``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogView:
                    Describes a view over log entries in
                a bucket.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseGetView._get_http_options()

            request, metadata = self._interceptor.pre_get_view(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseGetView._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseGetView._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.GetView",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetView",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._GetView._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogView()
            pb_resp = logging_config.LogView.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_get_view(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_get_view_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogView.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.get_view",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "GetView",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _ListBuckets(_BaseConfigServiceV2RestTransport._BaseListBuckets, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.ListBuckets")

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
                request: logging_config.ListBucketsRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.ListBucketsResponse:
            r"""Call the list buckets method over HTTP.

            Args:
                request (~.logging_config.ListBucketsRequest):
                    The request object. The parameters to ``ListBuckets``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.ListBucketsResponse:
                    The response from ListBuckets.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseListBuckets._get_http_options()

            request, metadata = self._interceptor.pre_list_buckets(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseListBuckets._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseListBuckets._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.ListBuckets",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListBuckets",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._ListBuckets._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.ListBucketsResponse()
            pb_resp = logging_config.ListBucketsResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_buckets(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_buckets_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.ListBucketsResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.list_buckets",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListBuckets",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _ListExclusions(_BaseConfigServiceV2RestTransport._BaseListExclusions, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.ListExclusions")

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
                request: logging_config.ListExclusionsRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.ListExclusionsResponse:
            r"""Call the list exclusions method over HTTP.

            Args:
                request (~.logging_config.ListExclusionsRequest):
                    The request object. The parameters to ``ListExclusions``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.ListExclusionsResponse:
                    Result returned from ``ListExclusions``.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseListExclusions._get_http_options()

            request, metadata = self._interceptor.pre_list_exclusions(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseListExclusions._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseListExclusions._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.ListExclusions",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListExclusions",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._ListExclusions._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.ListExclusionsResponse()
            pb_resp = logging_config.ListExclusionsResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_exclusions(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_exclusions_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.ListExclusionsResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.list_exclusions",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListExclusions",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _ListLinks(_BaseConfigServiceV2RestTransport._BaseListLinks, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.ListLinks")

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
                request: logging_config.ListLinksRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.ListLinksResponse:
            r"""Call the list links method over HTTP.

            Args:
                request (~.logging_config.ListLinksRequest):
                    The request object. The parameters to ListLinks.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.ListLinksResponse:
                    The response from ListLinks.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseListLinks._get_http_options()

            request, metadata = self._interceptor.pre_list_links(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseListLinks._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseListLinks._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.ListLinks",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListLinks",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._ListLinks._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.ListLinksResponse()
            pb_resp = logging_config.ListLinksResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_links(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_links_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.ListLinksResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.list_links",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListLinks",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _ListLogScopes(_BaseConfigServiceV2RestTransport._BaseListLogScopes, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.ListLogScopes")

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
                request: logging_config.ListLogScopesRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.ListLogScopesResponse:
            r"""Call the list log scopes method over HTTP.

            Args:
                request (~.logging_config.ListLogScopesRequest):
                    The request object. The parameters to ``ListLogScopes``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.ListLogScopesResponse:
                    The response from ``ListLogScopes``. Every project has a
                ``_Default`` log scope that cannot be modified or
                deleted.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseListLogScopes._get_http_options()

            request, metadata = self._interceptor.pre_list_log_scopes(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseListLogScopes._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseListLogScopes._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.ListLogScopes",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListLogScopes",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._ListLogScopes._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.ListLogScopesResponse()
            pb_resp = logging_config.ListLogScopesResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_log_scopes(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_log_scopes_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.ListLogScopesResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.list_log_scopes",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListLogScopes",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _ListRecentQueries(_BaseConfigServiceV2RestTransport._BaseListRecentQueries, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.ListRecentQueries")

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
                request: logging_config.ListRecentQueriesRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.ListRecentQueriesResponse:
            r"""Call the list recent queries method over HTTP.

            Args:
                request (~.logging_config.ListRecentQueriesRequest):
                    The request object. The parameters to
                'ListRecentQueries'.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.ListRecentQueriesResponse:
                    The response from ListRecentQueries.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseListRecentQueries._get_http_options()

            request, metadata = self._interceptor.pre_list_recent_queries(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseListRecentQueries._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseListRecentQueries._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.ListRecentQueries",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListRecentQueries",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._ListRecentQueries._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.ListRecentQueriesResponse()
            pb_resp = logging_config.ListRecentQueriesResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_recent_queries(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_recent_queries_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.ListRecentQueriesResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.list_recent_queries",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListRecentQueries",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _ListSavedQueries(_BaseConfigServiceV2RestTransport._BaseListSavedQueries, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.ListSavedQueries")

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
                request: logging_config.ListSavedQueriesRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.ListSavedQueriesResponse:
            r"""Call the list saved queries method over HTTP.

            Args:
                request (~.logging_config.ListSavedQueriesRequest):
                    The request object. The parameters to 'ListSavedQueries'.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.ListSavedQueriesResponse:
                    The response from ListSavedQueries.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseListSavedQueries._get_http_options()

            request, metadata = self._interceptor.pre_list_saved_queries(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseListSavedQueries._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseListSavedQueries._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.ListSavedQueries",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListSavedQueries",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._ListSavedQueries._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.ListSavedQueriesResponse()
            pb_resp = logging_config.ListSavedQueriesResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_saved_queries(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_saved_queries_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.ListSavedQueriesResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.list_saved_queries",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListSavedQueries",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _ListSinks(_BaseConfigServiceV2RestTransport._BaseListSinks, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.ListSinks")

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
                request: logging_config.ListSinksRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.ListSinksResponse:
            r"""Call the list sinks method over HTTP.

            Args:
                request (~.logging_config.ListSinksRequest):
                    The request object. The parameters to ``ListSinks``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.ListSinksResponse:
                    Result returned from ``ListSinks``.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseListSinks._get_http_options()

            request, metadata = self._interceptor.pre_list_sinks(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseListSinks._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseListSinks._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.ListSinks",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListSinks",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._ListSinks._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.ListSinksResponse()
            pb_resp = logging_config.ListSinksResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_sinks(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_sinks_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.ListSinksResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.list_sinks",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListSinks",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _ListViews(_BaseConfigServiceV2RestTransport._BaseListViews, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.ListViews")

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
                request: logging_config.ListViewsRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.ListViewsResponse:
            r"""Call the list views method over HTTP.

            Args:
                request (~.logging_config.ListViewsRequest):
                    The request object. The parameters to ``ListViews``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.ListViewsResponse:
                    The response from ListViews.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseListViews._get_http_options()

            request, metadata = self._interceptor.pre_list_views(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseListViews._get_transcoded_request(http_options, request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseListViews._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.ListViews",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListViews",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._ListViews._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.ListViewsResponse()
            pb_resp = logging_config.ListViewsResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_list_views(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_list_views_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.ListViewsResponse.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.list_views",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "ListViews",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _UndeleteBucket(_BaseConfigServiceV2RestTransport._BaseUndeleteBucket, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.UndeleteBucket")

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
                request: logging_config.UndeleteBucketRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ):
            r"""Call the undelete bucket method over HTTP.

            Args:
                request (~.logging_config.UndeleteBucketRequest):
                    The request object. The parameters to ``UndeleteBucket``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.
            """

            http_options = _BaseConfigServiceV2RestTransport._BaseUndeleteBucket._get_http_options()

            request, metadata = self._interceptor.pre_undelete_bucket(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseUndeleteBucket._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseUndeleteBucket._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseUndeleteBucket._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.UndeleteBucket",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UndeleteBucket",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._UndeleteBucket._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

    class _UpdateBucket(_BaseConfigServiceV2RestTransport._BaseUpdateBucket, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.UpdateBucket")

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
                request: logging_config.UpdateBucketRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogBucket:
            r"""Call the update bucket method over HTTP.

            Args:
                request (~.logging_config.UpdateBucketRequest):
                    The request object. The parameters to ``UpdateBucket``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogBucket:
                    Describes a repository in which log
                entries are stored.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseUpdateBucket._get_http_options()

            request, metadata = self._interceptor.pre_update_bucket(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseUpdateBucket._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseUpdateBucket._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseUpdateBucket._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.UpdateBucket",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateBucket",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._UpdateBucket._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogBucket()
            pb_resp = logging_config.LogBucket.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_update_bucket(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_update_bucket_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogBucket.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.update_bucket",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateBucket",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _UpdateBucketAsync(_BaseConfigServiceV2RestTransport._BaseUpdateBucketAsync, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.UpdateBucketAsync")

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
                request: logging_config.UpdateBucketRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> operations_pb2.Operation:
            r"""Call the update bucket async method over HTTP.

            Args:
                request (~.logging_config.UpdateBucketRequest):
                    The request object. The parameters to ``UpdateBucket``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.operations_pb2.Operation:
                    This resource represents a
                long-running operation that is the
                result of a network API call.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseUpdateBucketAsync._get_http_options()

            request, metadata = self._interceptor.pre_update_bucket_async(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseUpdateBucketAsync._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseUpdateBucketAsync._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseUpdateBucketAsync._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.UpdateBucketAsync",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateBucketAsync",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._UpdateBucketAsync._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = operations_pb2.Operation()
            json_format.Parse(response.content, resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_update_bucket_async(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_update_bucket_async_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = json_format.MessageToJson(resp)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.update_bucket_async",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateBucketAsync",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _UpdateCmekSettings(_BaseConfigServiceV2RestTransport._BaseUpdateCmekSettings, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.UpdateCmekSettings")

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
                request: logging_config.UpdateCmekSettingsRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.CmekSettings:
            r"""Call the update cmek settings method over HTTP.

            Args:
                request (~.logging_config.UpdateCmekSettingsRequest):
                    The request object. The parameters to
                [UpdateCmekSettings][google.logging.v2.ConfigServiceV2.UpdateCmekSettings].

                See `Configure CMEK for Cloud
                Logging <https://docs.cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.CmekSettings:
                    Describes the customer-managed encryption key (CMEK)
                settings associated with a project, folder,
                organization, billing account, or flexible resource.

                Note: CMEK for the Log Router can currently only be
                configured for Google Cloud organizations. Once
                configured, it applies to all projects and folders in
                the Google Cloud organization.

                See `Configure CMEK for Cloud
                Logging <https://docs.cloud.google.com/logging/docs/routing/managed-encryption>`__
                for more information.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseUpdateCmekSettings._get_http_options()

            request, metadata = self._interceptor.pre_update_cmek_settings(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseUpdateCmekSettings._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseUpdateCmekSettings._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseUpdateCmekSettings._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.UpdateCmekSettings",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateCmekSettings",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._UpdateCmekSettings._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.CmekSettings()
            pb_resp = logging_config.CmekSettings.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_update_cmek_settings(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_update_cmek_settings_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.CmekSettings.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.update_cmek_settings",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateCmekSettings",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _UpdateExclusion(_BaseConfigServiceV2RestTransport._BaseUpdateExclusion, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.UpdateExclusion")

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
                request: logging_config.UpdateExclusionRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogExclusion:
            r"""Call the update exclusion method over HTTP.

            Args:
                request (~.logging_config.UpdateExclusionRequest):
                    The request object. The parameters to ``UpdateExclusion``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogExclusion:
                    Specifies a set of log entries that are filtered out by
                a sink. If your Google Cloud resource receives a large
                volume of log entries, you can use exclusions to reduce
                your chargeable logs. Note that exclusions on
                organization-level and folder-level sinks don't apply to
                child resources. Note also that you cannot modify the
                \_Required sink or exclude logs from it.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseUpdateExclusion._get_http_options()

            request, metadata = self._interceptor.pre_update_exclusion(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseUpdateExclusion._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseUpdateExclusion._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseUpdateExclusion._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.UpdateExclusion",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateExclusion",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._UpdateExclusion._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogExclusion()
            pb_resp = logging_config.LogExclusion.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_update_exclusion(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_update_exclusion_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogExclusion.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.update_exclusion",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateExclusion",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _UpdateLogScope(_BaseConfigServiceV2RestTransport._BaseUpdateLogScope, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.UpdateLogScope")

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
                request: logging_config.UpdateLogScopeRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogScope:
            r"""Call the update log scope method over HTTP.

            Args:
                request (~.logging_config.UpdateLogScopeRequest):
                    The request object. The parameters to ``UpdateLogScope``. The ``_Default``
                log scope cannot be modified.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogScope:
                    Describes a group of resources to
                read log entries from.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseUpdateLogScope._get_http_options()

            request, metadata = self._interceptor.pre_update_log_scope(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseUpdateLogScope._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseUpdateLogScope._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseUpdateLogScope._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.UpdateLogScope",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateLogScope",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._UpdateLogScope._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogScope()
            pb_resp = logging_config.LogScope.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_update_log_scope(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_update_log_scope_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogScope.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.update_log_scope",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateLogScope",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _UpdateSavedQuery(_BaseConfigServiceV2RestTransport._BaseUpdateSavedQuery, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.UpdateSavedQuery")

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
                request: logging_config.UpdateSavedQueryRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.SavedQuery:
            r"""Call the update saved query method over HTTP.

            Args:
                request (~.logging_config.UpdateSavedQueryRequest):
                    The request object. The parameters to 'UpdateSavedQuery'.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.SavedQuery:
                    Describes a query that has been saved
                by a user.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseUpdateSavedQuery._get_http_options()

            request, metadata = self._interceptor.pre_update_saved_query(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseUpdateSavedQuery._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseUpdateSavedQuery._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseUpdateSavedQuery._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.UpdateSavedQuery",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateSavedQuery",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._UpdateSavedQuery._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.SavedQuery()
            pb_resp = logging_config.SavedQuery.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_update_saved_query(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_update_saved_query_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.SavedQuery.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.update_saved_query",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateSavedQuery",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _UpdateSettings(_BaseConfigServiceV2RestTransport._BaseUpdateSettings, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.UpdateSettings")

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
                request: logging_config.UpdateSettingsRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.Settings:
            r"""Call the update settings method over HTTP.

            Args:
                request (~.logging_config.UpdateSettingsRequest):
                    The request object. The parameters to
                [UpdateSettings][google.logging.v2.ConfigServiceV2.UpdateSettings].

                See [Configure default settings for organizations and
                folders]
                (https://docs.cloud.google.com/logging/docs/default-settings)
                for more information.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.Settings:
                    Describes the settings associated
                with a project, folder, organization, or
                billing account.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseUpdateSettings._get_http_options()

            request, metadata = self._interceptor.pre_update_settings(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseUpdateSettings._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseUpdateSettings._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseUpdateSettings._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.UpdateSettings",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateSettings",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._UpdateSettings._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.Settings()
            pb_resp = logging_config.Settings.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_update_settings(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_update_settings_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.Settings.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.update_settings",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateSettings",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _UpdateSink(_BaseConfigServiceV2RestTransport._BaseUpdateSink, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.UpdateSink")

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
                request: logging_config.UpdateSinkRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogSink:
            r"""Call the update sink method over HTTP.

            Args:
                request (~.logging_config.UpdateSinkRequest):
                    The request object. The parameters to ``UpdateSink``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogSink:
                    Describes a sink used to export log entries to one of
                the following destinations:

                - a Cloud Logging log bucket,
                - a Cloud Storage bucket,
                - a BigQuery dataset,
                - a Pub/Sub topic,
                - a Cloud project.

                A logs filter controls which log entries are exported.
                The sink must be created within a project, organization,
                billing account, or folder.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseUpdateSink._get_http_options()

            request, metadata = self._interceptor.pre_update_sink(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseUpdateSink._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseUpdateSink._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseUpdateSink._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.UpdateSink",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateSink",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._UpdateSink._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogSink()
            pb_resp = logging_config.LogSink.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_update_sink(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_update_sink_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogSink.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.update_sink",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateSink",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    class _UpdateView(_BaseConfigServiceV2RestTransport._BaseUpdateView, ConfigServiceV2RestStub):
        def __hash__(self):
            return hash("ConfigServiceV2RestTransport.UpdateView")

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
                request: logging_config.UpdateViewRequest, *,
                retry: OptionalRetry=gapic_v1.method.DEFAULT,
                timeout: Optional[float]=None,
                metadata: Sequence[Tuple[str, Union[str, bytes]]]=(),
                ) -> logging_config.LogView:
            r"""Call the update view method over HTTP.

            Args:
                request (~.logging_config.UpdateViewRequest):
                    The request object. The parameters to ``UpdateView``.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                    sent along with the request as metadata. Normally, each value must be of type `str`,
                    but for metadata keys ending with the suffix `-bin`, the corresponding values must
                    be of type `bytes`.

            Returns:
                ~.logging_config.LogView:
                    Describes a view over log entries in
                a bucket.

            """

            http_options = _BaseConfigServiceV2RestTransport._BaseUpdateView._get_http_options()

            request, metadata = self._interceptor.pre_update_view(request, metadata)
            transcoded_request = _BaseConfigServiceV2RestTransport._BaseUpdateView._get_transcoded_request(http_options, request)

            body = _BaseConfigServiceV2RestTransport._BaseUpdateView._get_request_body_json(transcoded_request)

            # Jsonify the query params
            query_params = _BaseConfigServiceV2RestTransport._BaseUpdateView._get_query_params_json(transcoded_request)

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
                    f"Sending request for google.logging_v2.ConfigServiceV2Client.UpdateView",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateView",
                        "httpRequest": http_request,
                        "metadata": http_request["headers"],
                    },
                )

            # Send the request
            response = ConfigServiceV2RestTransport._UpdateView._get_response(self._host, metadata, query_params, self._session, timeout, transcoded_request, body)

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = logging_config.LogView()
            pb_resp = logging_config.LogView.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)

            resp = self._interceptor.post_update_view(resp)
            response_metadata = [(k, str(v)) for k, v in response.headers.items()]
            resp, _ = self._interceptor.post_update_view_with_metadata(resp, response_metadata)
            if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(logging.DEBUG):  # pragma: NO COVER
                try:
                    response_payload = logging_config.LogView.to_json(response)
                except:
                    response_payload = None
                http_response = {
                "payload": response_payload,
                "headers":  dict(response.headers),
                "status": response.status_code,
                }
                _LOGGER.debug(
                    "Received response for google.logging_v2.ConfigServiceV2Client.update_view",
                    extra = {
                        "serviceName": "google.logging.v2.ConfigServiceV2",
                        "rpcName": "UpdateView",
                        "metadata": http_response["headers"],
                        "httpResponse": http_response,
                    },
                )
            return resp

    @property
    def copy_log_entries(self) -> Callable[
            [logging_config.CopyLogEntriesRequest],
            operations_pb2.Operation]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CopyLogEntries(self._session, self._host, self._interceptor) # type: ignore

    @property
    def create_bucket(self) -> Callable[
            [logging_config.CreateBucketRequest],
            logging_config.LogBucket]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CreateBucket(self._session, self._host, self._interceptor) # type: ignore

    @property
    def create_bucket_async(self) -> Callable[
            [logging_config.CreateBucketRequest],
            operations_pb2.Operation]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CreateBucketAsync(self._session, self._host, self._interceptor) # type: ignore

    @property
    def create_exclusion(self) -> Callable[
            [logging_config.CreateExclusionRequest],
            logging_config.LogExclusion]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CreateExclusion(self._session, self._host, self._interceptor) # type: ignore

    @property
    def create_link(self) -> Callable[
            [logging_config.CreateLinkRequest],
            operations_pb2.Operation]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CreateLink(self._session, self._host, self._interceptor) # type: ignore

    @property
    def create_log_scope(self) -> Callable[
            [logging_config.CreateLogScopeRequest],
            logging_config.LogScope]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CreateLogScope(self._session, self._host, self._interceptor) # type: ignore

    @property
    def create_saved_query(self) -> Callable[
            [logging_config.CreateSavedQueryRequest],
            logging_config.SavedQuery]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CreateSavedQuery(self._session, self._host, self._interceptor) # type: ignore

    @property
    def create_sink(self) -> Callable[
            [logging_config.CreateSinkRequest],
            logging_config.LogSink]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CreateSink(self._session, self._host, self._interceptor) # type: ignore

    @property
    def create_view(self) -> Callable[
            [logging_config.CreateViewRequest],
            logging_config.LogView]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CreateView(self._session, self._host, self._interceptor) # type: ignore

    @property
    def delete_bucket(self) -> Callable[
            [logging_config.DeleteBucketRequest],
            empty_pb2.Empty]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteBucket(self._session, self._host, self._interceptor) # type: ignore

    @property
    def delete_exclusion(self) -> Callable[
            [logging_config.DeleteExclusionRequest],
            empty_pb2.Empty]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteExclusion(self._session, self._host, self._interceptor) # type: ignore

    @property
    def delete_link(self) -> Callable[
            [logging_config.DeleteLinkRequest],
            operations_pb2.Operation]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteLink(self._session, self._host, self._interceptor) # type: ignore

    @property
    def delete_log_scope(self) -> Callable[
            [logging_config.DeleteLogScopeRequest],
            empty_pb2.Empty]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteLogScope(self._session, self._host, self._interceptor) # type: ignore

    @property
    def delete_saved_query(self) -> Callable[
            [logging_config.DeleteSavedQueryRequest],
            empty_pb2.Empty]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteSavedQuery(self._session, self._host, self._interceptor) # type: ignore

    @property
    def delete_sink(self) -> Callable[
            [logging_config.DeleteSinkRequest],
            empty_pb2.Empty]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteSink(self._session, self._host, self._interceptor) # type: ignore

    @property
    def delete_view(self) -> Callable[
            [logging_config.DeleteViewRequest],
            empty_pb2.Empty]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteView(self._session, self._host, self._interceptor) # type: ignore

    @property
    def get_bucket(self) -> Callable[
            [logging_config.GetBucketRequest],
            logging_config.LogBucket]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetBucket(self._session, self._host, self._interceptor) # type: ignore

    @property
    def get_cmek_settings(self) -> Callable[
            [logging_config.GetCmekSettingsRequest],
            logging_config.CmekSettings]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetCmekSettings(self._session, self._host, self._interceptor) # type: ignore

    @property
    def get_exclusion(self) -> Callable[
            [logging_config.GetExclusionRequest],
            logging_config.LogExclusion]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetExclusion(self._session, self._host, self._interceptor) # type: ignore

    @property
    def get_link(self) -> Callable[
            [logging_config.GetLinkRequest],
            logging_config.Link]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetLink(self._session, self._host, self._interceptor) # type: ignore

    @property
    def get_log_scope(self) -> Callable[
            [logging_config.GetLogScopeRequest],
            logging_config.LogScope]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetLogScope(self._session, self._host, self._interceptor) # type: ignore

    @property
    def get_saved_query(self) -> Callable[
            [logging_config.GetSavedQueryRequest],
            logging_config.SavedQuery]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetSavedQuery(self._session, self._host, self._interceptor) # type: ignore

    @property
    def get_settings(self) -> Callable[
            [logging_config.GetSettingsRequest],
            logging_config.Settings]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetSettings(self._session, self._host, self._interceptor) # type: ignore

    @property
    def get_sink(self) -> Callable[
            [logging_config.GetSinkRequest],
            logging_config.LogSink]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetSink(self._session, self._host, self._interceptor) # type: ignore

    @property
    def get_view(self) -> Callable[
            [logging_config.GetViewRequest],
            logging_config.LogView]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetView(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_buckets(self) -> Callable[
            [logging_config.ListBucketsRequest],
            logging_config.ListBucketsResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListBuckets(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_exclusions(self) -> Callable[
            [logging_config.ListExclusionsRequest],
            logging_config.ListExclusionsResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListExclusions(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_links(self) -> Callable[
            [logging_config.ListLinksRequest],
            logging_config.ListLinksResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListLinks(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_log_scopes(self) -> Callable[
            [logging_config.ListLogScopesRequest],
            logging_config.ListLogScopesResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListLogScopes(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_recent_queries(self) -> Callable[
            [logging_config.ListRecentQueriesRequest],
            logging_config.ListRecentQueriesResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListRecentQueries(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_saved_queries(self) -> Callable[
            [logging_config.ListSavedQueriesRequest],
            logging_config.ListSavedQueriesResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListSavedQueries(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_sinks(self) -> Callable[
            [logging_config.ListSinksRequest],
            logging_config.ListSinksResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListSinks(self._session, self._host, self._interceptor) # type: ignore

    @property
    def list_views(self) -> Callable[
            [logging_config.ListViewsRequest],
            logging_config.ListViewsResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListViews(self._session, self._host, self._interceptor) # type: ignore

    @property
    def undelete_bucket(self) -> Callable[
            [logging_config.UndeleteBucketRequest],
            empty_pb2.Empty]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UndeleteBucket(self._session, self._host, self._interceptor) # type: ignore

    @property
    def update_bucket(self) -> Callable[
            [logging_config.UpdateBucketRequest],
            logging_config.LogBucket]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UpdateBucket(self._session, self._host, self._interceptor) # type: ignore

    @property
    def update_bucket_async(self) -> Callable[
            [logging_config.UpdateBucketRequest],
            operations_pb2.Operation]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UpdateBucketAsync(self._session, self._host, self._interceptor) # type: ignore

    @property
    def update_cmek_settings(self) -> Callable[
            [logging_config.UpdateCmekSettingsRequest],
            logging_config.CmekSettings]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UpdateCmekSettings(self._session, self._host, self._interceptor) # type: ignore

    @property
    def update_exclusion(self) -> Callable[
            [logging_config.UpdateExclusionRequest],
            logging_config.LogExclusion]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UpdateExclusion(self._session, self._host, self._interceptor) # type: ignore

    @property
    def update_log_scope(self) -> Callable[
            [logging_config.UpdateLogScopeRequest],
            logging_config.LogScope]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UpdateLogScope(self._session, self._host, self._interceptor) # type: ignore

    @property
    def update_saved_query(self) -> Callable[
            [logging_config.UpdateSavedQueryRequest],
            logging_config.SavedQuery]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UpdateSavedQuery(self._session, self._host, self._interceptor) # type: ignore

    @property
    def update_settings(self) -> Callable[
            [logging_config.UpdateSettingsRequest],
            logging_config.Settings]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UpdateSettings(self._session, self._host, self._interceptor) # type: ignore

    @property
    def update_sink(self) -> Callable[
            [logging_config.UpdateSinkRequest],
            logging_config.LogSink]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UpdateSink(self._session, self._host, self._interceptor) # type: ignore

    @property
    def update_view(self) -> Callable[
            [logging_config.UpdateViewRequest],
            logging_config.LogView]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UpdateView(self._session, self._host, self._interceptor) # type: ignore

    @property
    def kind(self) -> str:
        return "rest"

    def close(self):
        self._session.close()


__all__=(
    'ConfigServiceV2RestTransport',
)
