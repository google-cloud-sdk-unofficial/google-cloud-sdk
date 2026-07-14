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
from collections import OrderedDict
import re
from typing import Dict, Callable, Mapping, MutableMapping, MutableSequence, Optional, Sequence, Tuple, Type, Union

from googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1 import gapic_version as package_version

from google.api_core.client_options import ClientOptions
from google.api_core import exceptions as core_exceptions
from google.api_core import gapic_v1
from google.api_core import retry_async as retries
from google.auth import credentials as ga_credentials   # type: ignore
from google.oauth2 import service_account              # type: ignore
import cloudsdk.google.protobuf


try:
    OptionalRetry = Union[retries.AsyncRetry, gapic_v1.method._MethodDefault, None]
except AttributeError:  # pragma: NO COVER
    OptionalRetry = Union[retries.AsyncRetry, object, None]  # type: ignore

from google.api_core import operation  # type: ignore
from google.api_core import operation_async  # type: ignore
from cloudsdk.google.protobuf import field_mask_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types import semantic_governance_policy_engine_service
from .transports.base import SemanticGovernancePolicyEngineServiceTransport, DEFAULT_CLIENT_INFO
from .transports.grpc_asyncio import SemanticGovernancePolicyEngineServiceGrpcAsyncIOTransport
from .client import SemanticGovernancePolicyEngineServiceClient

try:
    from google.api_core import client_logging  # type: ignore
    CLIENT_LOGGING_SUPPORTED = True  # pragma: NO COVER
except ImportError:  # pragma: NO COVER
    CLIENT_LOGGING_SUPPORTED = False

_LOGGER = std_logging.getLogger(__name__)

class SemanticGovernancePolicyEngineServiceAsyncClient:
    """Service for managing SemanticGovernancePolicyEngine
    resources.
    """

    _client: SemanticGovernancePolicyEngineServiceClient

    # Copy defaults from the synchronous client for use here.
    # Note: DEFAULT_ENDPOINT is deprecated. Use _DEFAULT_ENDPOINT_TEMPLATE instead.
    DEFAULT_ENDPOINT = SemanticGovernancePolicyEngineServiceClient.DEFAULT_ENDPOINT
    DEFAULT_MTLS_ENDPOINT = SemanticGovernancePolicyEngineServiceClient.DEFAULT_MTLS_ENDPOINT
    _DEFAULT_ENDPOINT_TEMPLATE = SemanticGovernancePolicyEngineServiceClient._DEFAULT_ENDPOINT_TEMPLATE
    _DEFAULT_UNIVERSE = SemanticGovernancePolicyEngineServiceClient._DEFAULT_UNIVERSE

    semantic_governance_policy_engine_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.semantic_governance_policy_engine_path)
    parse_semantic_governance_policy_engine_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.parse_semantic_governance_policy_engine_path)
    common_billing_account_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.common_billing_account_path)
    parse_common_billing_account_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.parse_common_billing_account_path)
    common_folder_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.common_folder_path)
    parse_common_folder_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.parse_common_folder_path)
    common_organization_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.common_organization_path)
    parse_common_organization_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.parse_common_organization_path)
    common_project_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.common_project_path)
    parse_common_project_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.parse_common_project_path)
    common_location_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.common_location_path)
    parse_common_location_path = staticmethod(SemanticGovernancePolicyEngineServiceClient.parse_common_location_path)

    @classmethod
    def from_service_account_info(cls, info: dict, *args, **kwargs):
        """Creates an instance of this client using the provided credentials
            info.

        Args:
            info (dict): The service account private key info.
            args: Additional arguments to pass to the constructor.
            kwargs: Additional arguments to pass to the constructor.

        Returns:
            SemanticGovernancePolicyEngineServiceAsyncClient: The constructed client.
        """
        return SemanticGovernancePolicyEngineServiceClient.from_service_account_info.__func__(SemanticGovernancePolicyEngineServiceAsyncClient, info, *args, **kwargs)  # type: ignore

    @classmethod
    def from_service_account_file(cls, filename: str, *args, **kwargs):
        """Creates an instance of this client using the provided credentials
            file.

        Args:
            filename (str): The path to the service account private key json
                file.
            args: Additional arguments to pass to the constructor.
            kwargs: Additional arguments to pass to the constructor.

        Returns:
            SemanticGovernancePolicyEngineServiceAsyncClient: The constructed client.
        """
        return SemanticGovernancePolicyEngineServiceClient.from_service_account_file.__func__(SemanticGovernancePolicyEngineServiceAsyncClient, filename, *args, **kwargs)  # type: ignore

    from_service_account_json = from_service_account_file

    @classmethod
    def get_mtls_endpoint_and_cert_source(cls, client_options: Optional[ClientOptions] = None):
        """Return the API endpoint and client cert source for mutual TLS.

        The client cert source is determined in the following order:
        (1) if `GOOGLE_API_USE_CLIENT_CERTIFICATE` environment variable is not "true", the
        client cert source is None.
        (2) if `client_options.client_cert_source` is provided, use the provided one; if the
        default client cert source exists, use the default one; otherwise the client cert
        source is None.

        The API endpoint is determined in the following order:
        (1) if `client_options.api_endpoint` if provided, use the provided one.
        (2) if `GOOGLE_API_USE_CLIENT_CERTIFICATE` environment variable is "always", use the
        default mTLS endpoint; if the environment variable is "never", use the default API
        endpoint; otherwise if client cert source exists, use the default mTLS endpoint, otherwise
        use the default API endpoint.

        More details can be found at https://google.aip.dev/auth/4114.

        Args:
            client_options (google.api_core.client_options.ClientOptions): Custom options for the
                client. Only the `api_endpoint` and `client_cert_source` properties may be used
                in this method.

        Returns:
            Tuple[str, Callable[[], Tuple[bytes, bytes]]]: returns the API endpoint and the
                client cert source to use.

        Raises:
            google.auth.exceptions.MutualTLSChannelError: If any errors happen.
        """
        return SemanticGovernancePolicyEngineServiceClient.get_mtls_endpoint_and_cert_source(client_options)  # type: ignore

    @property
    def transport(self) -> SemanticGovernancePolicyEngineServiceTransport:
        """Returns the transport used by the client instance.

        Returns:
            SemanticGovernancePolicyEngineServiceTransport: The transport used by the client instance.
        """
        return self._client.transport

    @property
    def api_endpoint(self):
        """Return the API endpoint used by the client instance.

        Returns:
            str: The API endpoint used by the client instance.
        """
        return self._client._api_endpoint

    @property
    def universe_domain(self) -> str:
        """Return the universe domain used by the client instance.

        Returns:
            str: The universe domain used
                by the client instance.
        """
        return self._client._universe_domain

    get_transport_class = SemanticGovernancePolicyEngineServiceClient.get_transport_class

    def __init__(self, *,
            credentials: Optional[ga_credentials.Credentials] = None,
            transport: Optional[Union[str, SemanticGovernancePolicyEngineServiceTransport, Callable[..., SemanticGovernancePolicyEngineServiceTransport]]] = "grpc_asyncio",
            client_options: Optional[ClientOptions] = None,
            client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
            ) -> None:
        """Instantiates the semantic governance policy engine service async client.

        Args:
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
            transport (Optional[Union[str,SemanticGovernancePolicyEngineServiceTransport,Callable[..., SemanticGovernancePolicyEngineServiceTransport]]]):
                The transport to use, or a Callable that constructs and returns a new transport to use.
                If a Callable is given, it will be called with the same set of initialization
                arguments as used in the SemanticGovernancePolicyEngineServiceTransport constructor.
                If set to None, a transport is chosen automatically.
                NOTE: "rest" transport functionality is currently in a
                beta state (preview). We welcome your feedback via an
                issue in this library's source repository.
            client_options (Optional[Union[google.api_core.client_options.ClientOptions, dict]]):
                Custom options for the client.

                1. The ``api_endpoint`` property can be used to override the
                default endpoint provided by the client when ``transport`` is
                not explicitly provided. Only if this property is not set and
                ``transport`` was not explicitly provided, the endpoint is
                determined by the GOOGLE_API_USE_MTLS_ENDPOINT environment
                variable, which have one of the following values:
                "always" (always use the default mTLS endpoint), "never" (always
                use the default regular endpoint) and "auto" (auto-switch to the
                default mTLS endpoint if client certificate is present; this is
                the default value).

                2. If the GOOGLE_API_USE_CLIENT_CERTIFICATE environment variable
                is "true", then the ``client_cert_source`` property can be used
                to provide a client certificate for mTLS transport. If
                not provided, the default SSL client certificate will be used if
                present. If GOOGLE_API_USE_CLIENT_CERTIFICATE is "false" or not
                set, no client certificate will be used.

                3. The ``universe_domain`` property can be used to override the
                default "googleapis.com" universe. Note that ``api_endpoint``
                property still takes precedence; and ``universe_domain`` is
                currently not supported for mTLS.

            client_info (google.api_core.gapic_v1.client_info.ClientInfo):
                The client info used to send a user-agent string along with
                API requests. If ``None``, then default info will be used.
                Generally, you only need to set this if you're developing
                your own client library.

        Raises:
            google.auth.exceptions.MutualTlsChannelError: If mutual TLS transport
                creation failed for any reason.
        """
        self._client = SemanticGovernancePolicyEngineServiceClient(
            credentials=credentials,
            transport=transport,
            client_options=client_options,
            client_info=client_info,

        )

        if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(std_logging.DEBUG):  # pragma: NO COVER
            _LOGGER.debug(
                "Created client `google.cloud.aiplatform_v1.SemanticGovernancePolicyEngineServiceAsyncClient`.",
                extra = {
                    "serviceName": "google.cloud.aiplatform.v1.SemanticGovernancePolicyEngineService",
                    "universeDomain": getattr(self._client._transport._credentials, "universe_domain", ""),
                    "credentialsType": f"{type(self._client._transport._credentials).__module__}.{type(self._client._transport._credentials).__qualname__}",
                    "credentialsInfo": getattr(self.transport._credentials, "get_cred_info", lambda: None)(),
                } if hasattr(self._client._transport, "_credentials") else {
                    "serviceName": "google.cloud.aiplatform.v1.SemanticGovernancePolicyEngineService",
                    "credentialsType": None,
                }
            )

    async def get_semantic_governance_policy_engine(self,
            request: Optional[Union[semantic_governance_policy_engine_service.GetSemanticGovernancePolicyEngineRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, Union[str, bytes]]] = (),
            ) -> semantic_governance_policy_engine_service.SemanticGovernancePolicyEngine:
        r"""Gets a SemanticGovernancePolicyEngine.

        A SemanticGovernancePolicyEngine is a singleton resource
        that is created when its parent is created, and deleted
        when its parent is deleted. This method retrieves the
        current state of the Semantic Governance Policy Engine.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import aiplatform_v1

            async def sample_get_semantic_governance_policy_engine():
                # Create a client
                client = aiplatform_v1.SemanticGovernancePolicyEngineServiceAsyncClient()

                # Initialize request argument(s)
                request = aiplatform_v1.GetSemanticGovernancePolicyEngineRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.get_semantic_governance_policy_engine(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.GetSemanticGovernancePolicyEngineRequest, dict]]):
                The request object. Request message for
                GetSemanticGovernancePolicyEngine.
            name (:class:`str`):
                Required. The resource name of the
                SemanticGovernancePolicyEngine to
                retrieve. Format:

                projects/{project}/locations/{location}/semanticGovernancePolicyEngine

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry_async.AsyncRetry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                sent along with the request as metadata. Normally, each value must be of type `str`,
                but for metadata keys ending with the suffix `-bin`, the corresponding values must
                be of type `bytes`.

        Returns:
            googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.SemanticGovernancePolicyEngine:
                Define a singleton
                SemanticGovernancePolicyEngine resource
                under a project and location.

        """
        # Create or coerce a protobuf request object.
        # - Quick check: If we got a request object, we should *not* have
        #   gotten any keyword arguments that map to the request.
        flattened_params = [name]
        has_flattened_params = len([param for param in flattened_params if param is not None]) > 0
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        # - Use the request object if provided (there's no risk of modifying the input as
        #   there are no flattened fields), or create one.
        if not isinstance(request, semantic_governance_policy_engine_service.GetSemanticGovernancePolicyEngineRequest):
            request = semantic_governance_policy_engine_service.GetSemanticGovernancePolicyEngineRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._client._transport._wrapped_methods[self._client._transport.get_semantic_governance_policy_engine]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
        )

        # Validate the universe domain.
        self._client._validate_universe_domain()

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def update_semantic_governance_policy_engine(self,
            request: Optional[Union[semantic_governance_policy_engine_service.UpdateSemanticGovernancePolicyEngineRequest, dict]] = None,
            *,
            semantic_governance_policy_engine: Optional[semantic_governance_policy_engine_service.SemanticGovernancePolicyEngine] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, Union[str, bytes]]] = (),
            ) -> operation_async.AsyncOperation:
        r"""Updates a SemanticGovernancePolicyEngine.

        This method performs an upsert operation. If the
        SemanticGovernancePolicyEngine resource does not exist,
        it will be created. Otherwise, it will be updated.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import aiplatform_v1

            async def sample_update_semantic_governance_policy_engine():
                # Create a client
                client = aiplatform_v1.SemanticGovernancePolicyEngineServiceAsyncClient()

                # Initialize request argument(s)
                request = aiplatform_v1.UpdateSemanticGovernancePolicyEngineRequest(
                )

                # Make the request
                operation = client.update_semantic_governance_policy_engine(request=request)

                print("Waiting for operation to complete...")

                response = (await operation).result()

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.UpdateSemanticGovernancePolicyEngineRequest, dict]]):
                The request object. Request message for
                UpdateSemanticGovernancePolicyEngine.
            semantic_governance_policy_engine (:class:`googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.SemanticGovernancePolicyEngine`):
                Required. The SemanticGovernancePolicyEngine resource to
                update. The name field of the
                semantic_governance_policy_engine must be of the form
                ``projects/{project}/locations/{location}/semanticGovernancePolicyEngine``.

                This corresponds to the ``semantic_governance_policy_engine`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
                Optional. Specifies the fields to be overwritten in the
                SemanticGovernancePolicyEngine resource by the update.
                The fields specified in the update_mask are relative to
                the resource itself. If no update_mask is provided, all
                fields are overwritten.

                This corresponds to the ``update_mask`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry_async.AsyncRetry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                sent along with the request as metadata. Normally, each value must be of type `str`,
                but for metadata keys ending with the suffix `-bin`, the corresponding values must
                be of type `bytes`.

        Returns:
            google.api_core.operation_async.AsyncOperation:
                An object representing a long-running operation.

                The result type for the operation will be :class:`googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.SemanticGovernancePolicyEngine` Define a singleton SemanticGovernancePolicyEngine resource
                   under a project and location.

        """
        # Create or coerce a protobuf request object.
        # - Quick check: If we got a request object, we should *not* have
        #   gotten any keyword arguments that map to the request.
        flattened_params = [semantic_governance_policy_engine, update_mask]
        has_flattened_params = len([param for param in flattened_params if param is not None]) > 0
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        # - Use the request object if provided (there's no risk of modifying the input as
        #   there are no flattened fields), or create one.
        if not isinstance(request, semantic_governance_policy_engine_service.UpdateSemanticGovernancePolicyEngineRequest):
            request = semantic_governance_policy_engine_service.UpdateSemanticGovernancePolicyEngineRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if semantic_governance_policy_engine is not None:
            request.semantic_governance_policy_engine = semantic_governance_policy_engine
        if update_mask is not None:
            request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._client._transport._wrapped_methods[self._client._transport.update_semantic_governance_policy_engine]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("semantic_governance_policy_engine.name", request.semantic_governance_policy_engine.name),
            )),
        )

        # Validate the universe domain.
        self._client._validate_universe_domain()

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Wrap the response in an operation future.
        response = operation_async.from_gapic(
            response,
            self._client._transport.operations_client,
            semantic_governance_policy_engine_service.SemanticGovernancePolicyEngine,
            metadata_type=semantic_governance_policy_engine_service.UpdateSemanticGovernancePolicyEngineOperationMetadata,
        )

        # Done; return the response.
        return response

    async def deprovision_semantic_governance_policy_engine(self,
            request: Optional[Union[semantic_governance_policy_engine_service.DeprovisionSemanticGovernancePolicyEngineRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, Union[str, bytes]]] = (),
            ) -> operation_async.AsyncOperation:
        r"""Deprovisions the SemanticGovernancePolicyEngine,
        tearing down the associated tenant project, GKE cluster,
        and PSC service attachments. This operation is
        irreversible.

        Returns a long-running operation; poll for completion.
        The response contains the SemanticGovernancePolicyEngine
        in DEPROVISIONING state.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import aiplatform_v1

            async def sample_deprovision_semantic_governance_policy_engine():
                # Create a client
                client = aiplatform_v1.SemanticGovernancePolicyEngineServiceAsyncClient()

                # Initialize request argument(s)
                request = aiplatform_v1.DeprovisionSemanticGovernancePolicyEngineRequest(
                    name="name_value",
                )

                # Make the request
                operation = client.deprovision_semantic_governance_policy_engine(request=request)

                print("Waiting for operation to complete...")

                response = (await operation).result()

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.DeprovisionSemanticGovernancePolicyEngineRequest, dict]]):
                The request object. Request message for
                [SemanticGovernancePolicyEngineService.DeprovisionSemanticGovernancePolicyEngine][google.cloud.aiplatform.v1.SemanticGovernancePolicyEngineService.DeprovisionSemanticGovernancePolicyEngine].
            name (:class:`str`):
                Required. The resource name of the
                SemanticGovernancePolicyEngine to
                deprovision. Format:

                projects/{project}/locations/{location}/semanticGovernancePolicyEngine

                This corresponds to the ``name`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            retry (google.api_core.retry_async.AsyncRetry): Designation of what errors, if any,
                should be retried.
            timeout (float): The timeout for this request.
            metadata (Sequence[Tuple[str, Union[str, bytes]]]): Key/value pairs which should be
                sent along with the request as metadata. Normally, each value must be of type `str`,
                but for metadata keys ending with the suffix `-bin`, the corresponding values must
                be of type `bytes`.

        Returns:
            google.api_core.operation_async.AsyncOperation:
                An object representing a long-running operation.

                The result type for the operation will be :class:`googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1.types.SemanticGovernancePolicyEngine` Define a singleton SemanticGovernancePolicyEngine resource
                   under a project and location.

        """
        # Create or coerce a protobuf request object.
        # - Quick check: If we got a request object, we should *not* have
        #   gotten any keyword arguments that map to the request.
        flattened_params = [name]
        has_flattened_params = len([param for param in flattened_params if param is not None]) > 0
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        # - Use the request object if provided (there's no risk of modifying the input as
        #   there are no flattened fields), or create one.
        if not isinstance(request, semantic_governance_policy_engine_service.DeprovisionSemanticGovernancePolicyEngineRequest):
            request = semantic_governance_policy_engine_service.DeprovisionSemanticGovernancePolicyEngineRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._client._transport._wrapped_methods[self._client._transport.deprovision_semantic_governance_policy_engine]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("name", request.name),
            )),
        )

        # Validate the universe domain.
        self._client._validate_universe_domain()

        # Send the request.
        response = await rpc(
            request,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Wrap the response in an operation future.
        response = operation_async.from_gapic(
            response,
            self._client._transport.operations_client,
            semantic_governance_policy_engine_service.SemanticGovernancePolicyEngine,
            metadata_type=semantic_governance_policy_engine_service.DeprovisionSemanticGovernancePolicyEngineOperationMetadata,
        )

        # Done; return the response.
        return response

    async def __aenter__(self) -> "SemanticGovernancePolicyEngineServiceAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.transport.close()

DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(gapic_version=package_version.__version__)

if hasattr(DEFAULT_CLIENT_INFO, "protobuf_runtime_version"):   # pragma: NO COVER
    DEFAULT_CLIENT_INFO.protobuf_runtime_version = cloudsdk.google.protobuf.__version__


__all__ = (
    "SemanticGovernancePolicyEngineServiceAsyncClient",
)
