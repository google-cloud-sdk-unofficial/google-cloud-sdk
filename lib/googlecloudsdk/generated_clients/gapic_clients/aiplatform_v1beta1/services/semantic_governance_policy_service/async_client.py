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

from googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1 import gapic_version as package_version

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
from cloudsdk.google.protobuf import empty_pb2  # type: ignore
from cloudsdk.google.protobuf import field_mask_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.services.semantic_governance_policy_service import pagers
from googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types import semantic_governance_policy_service
from .transports.base import SemanticGovernancePolicyServiceTransport, DEFAULT_CLIENT_INFO
from .transports.grpc_asyncio import SemanticGovernancePolicyServiceGrpcAsyncIOTransport
from .client import SemanticGovernancePolicyServiceClient

try:
    from google.api_core import client_logging  # type: ignore
    CLIENT_LOGGING_SUPPORTED = True  # pragma: NO COVER
except ImportError:  # pragma: NO COVER
    CLIENT_LOGGING_SUPPORTED = False

_LOGGER = std_logging.getLogger(__name__)

class SemanticGovernancePolicyServiceAsyncClient:
    """Manages SemanticGovernancePolicies.
    A SemanticGovernancePolicy is a resource that represents a
    collection of Agents and Models that are sold together as part
    of a single product.
    """

    _client: SemanticGovernancePolicyServiceClient

    # Copy defaults from the synchronous client for use here.
    # Note: DEFAULT_ENDPOINT is deprecated. Use _DEFAULT_ENDPOINT_TEMPLATE instead.
    DEFAULT_ENDPOINT = SemanticGovernancePolicyServiceClient.DEFAULT_ENDPOINT
    DEFAULT_MTLS_ENDPOINT = SemanticGovernancePolicyServiceClient.DEFAULT_MTLS_ENDPOINT
    _DEFAULT_ENDPOINT_TEMPLATE = SemanticGovernancePolicyServiceClient._DEFAULT_ENDPOINT_TEMPLATE
    _DEFAULT_UNIVERSE = SemanticGovernancePolicyServiceClient._DEFAULT_UNIVERSE

    semantic_governance_policy_path = staticmethod(SemanticGovernancePolicyServiceClient.semantic_governance_policy_path)
    parse_semantic_governance_policy_path = staticmethod(SemanticGovernancePolicyServiceClient.parse_semantic_governance_policy_path)
    common_billing_account_path = staticmethod(SemanticGovernancePolicyServiceClient.common_billing_account_path)
    parse_common_billing_account_path = staticmethod(SemanticGovernancePolicyServiceClient.parse_common_billing_account_path)
    common_folder_path = staticmethod(SemanticGovernancePolicyServiceClient.common_folder_path)
    parse_common_folder_path = staticmethod(SemanticGovernancePolicyServiceClient.parse_common_folder_path)
    common_organization_path = staticmethod(SemanticGovernancePolicyServiceClient.common_organization_path)
    parse_common_organization_path = staticmethod(SemanticGovernancePolicyServiceClient.parse_common_organization_path)
    common_project_path = staticmethod(SemanticGovernancePolicyServiceClient.common_project_path)
    parse_common_project_path = staticmethod(SemanticGovernancePolicyServiceClient.parse_common_project_path)
    common_location_path = staticmethod(SemanticGovernancePolicyServiceClient.common_location_path)
    parse_common_location_path = staticmethod(SemanticGovernancePolicyServiceClient.parse_common_location_path)

    @classmethod
    def from_service_account_info(cls, info: dict, *args, **kwargs):
        """Creates an instance of this client using the provided credentials
            info.

        Args:
            info (dict): The service account private key info.
            args: Additional arguments to pass to the constructor.
            kwargs: Additional arguments to pass to the constructor.

        Returns:
            SemanticGovernancePolicyServiceAsyncClient: The constructed client.
        """
        return SemanticGovernancePolicyServiceClient.from_service_account_info.__func__(SemanticGovernancePolicyServiceAsyncClient, info, *args, **kwargs)  # type: ignore

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
            SemanticGovernancePolicyServiceAsyncClient: The constructed client.
        """
        return SemanticGovernancePolicyServiceClient.from_service_account_file.__func__(SemanticGovernancePolicyServiceAsyncClient, filename, *args, **kwargs)  # type: ignore

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
        return SemanticGovernancePolicyServiceClient.get_mtls_endpoint_and_cert_source(client_options)  # type: ignore

    @property
    def transport(self) -> SemanticGovernancePolicyServiceTransport:
        """Returns the transport used by the client instance.

        Returns:
            SemanticGovernancePolicyServiceTransport: The transport used by the client instance.
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

    get_transport_class = SemanticGovernancePolicyServiceClient.get_transport_class

    def __init__(self, *,
            credentials: Optional[ga_credentials.Credentials] = None,
            transport: Optional[Union[str, SemanticGovernancePolicyServiceTransport, Callable[..., SemanticGovernancePolicyServiceTransport]]] = "grpc_asyncio",
            client_options: Optional[ClientOptions] = None,
            client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
            ) -> None:
        """Instantiates the semantic governance policy service async client.

        Args:
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
            transport (Optional[Union[str,SemanticGovernancePolicyServiceTransport,Callable[..., SemanticGovernancePolicyServiceTransport]]]):
                The transport to use, or a Callable that constructs and returns a new transport to use.
                If a Callable is given, it will be called with the same set of initialization
                arguments as used in the SemanticGovernancePolicyServiceTransport constructor.
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
        self._client = SemanticGovernancePolicyServiceClient(
            credentials=credentials,
            transport=transport,
            client_options=client_options,
            client_info=client_info,

        )

        if CLIENT_LOGGING_SUPPORTED and _LOGGER.isEnabledFor(std_logging.DEBUG):  # pragma: NO COVER
            _LOGGER.debug(
                "Created client `google.cloud.aiplatform_v1beta1.SemanticGovernancePolicyServiceAsyncClient`.",
                extra = {
                    "serviceName": "google.cloud.aiplatform.v1beta1.SemanticGovernancePolicyService",
                    "universeDomain": getattr(self._client._transport._credentials, "universe_domain", ""),
                    "credentialsType": f"{type(self._client._transport._credentials).__module__}.{type(self._client._transport._credentials).__qualname__}",
                    "credentialsInfo": getattr(self.transport._credentials, "get_cred_info", lambda: None)(),
                } if hasattr(self._client._transport, "_credentials") else {
                    "serviceName": "google.cloud.aiplatform.v1beta1.SemanticGovernancePolicyService",
                    "credentialsType": None,
                }
            )

    async def create_semantic_governance_policy(self,
            request: Optional[Union[semantic_governance_policy_service.CreateSemanticGovernancePolicyRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            semantic_governance_policy: Optional[semantic_governance_policy_service.SemanticGovernancePolicy] = None,
            semantic_governance_policy_id: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, Union[str, bytes]]] = (),
            ) -> operation_async.AsyncOperation:
        r"""Creates a SemanticGovernancePolicy.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import aiplatform_v1beta1

            async def sample_create_semantic_governance_policy():
                # Create a client
                client = aiplatform_v1beta1.SemanticGovernancePolicyServiceAsyncClient()

                # Initialize request argument(s)
                semantic_governance_policy = aiplatform_v1beta1.SemanticGovernancePolicy()
                semantic_governance_policy.natural_language_constraint = "natural_language_constraint_value"
                semantic_governance_policy.agent = "agent_value"

                request = aiplatform_v1beta1.CreateSemanticGovernancePolicyRequest(
                    parent="parent_value",
                    semantic_governance_policy=semantic_governance_policy,
                    semantic_governance_policy_id="semantic_governance_policy_id_value",
                )

                # Make the request
                operation = client.create_semantic_governance_policy(request=request)

                print("Waiting for operation to complete...")

                response = (await operation).result()

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.CreateSemanticGovernancePolicyRequest, dict]]):
                The request object. Request message for
                SemanticGovernancePolicyService.CreateSemanticGovernancePolicy.
            parent (:class:`str`):
                Required. The resource name of the Location into which
                to create the SemanticGovernancePolicy. Format:
                ``projects/{project}/locations/{location}``

                This corresponds to the ``parent`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            semantic_governance_policy (:class:`googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.SemanticGovernancePolicy`):
                Required. The
                SemanticGovernancePolicy to create.

                This corresponds to the ``semantic_governance_policy`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            semantic_governance_policy_id (:class:`str`):
                Required. The ID to use for the
                SemanticGovernancePolicy, which will become the final
                component of the SemanticGovernancePolicy's resource
                name.

                This value may be up to 63 characters, and valid
                characters are ``[a-z0-9-]``. The first character cannot
                be a number or hyphen. The last character must be a
                letter or a number.

                This corresponds to the ``semantic_governance_policy_id`` field
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

                The result type for the operation will be :class:`googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.SemanticGovernancePolicy` Represents a governance policy applied to a specific Agent and optionally
                   a specific Tool within that Agent.

        """
        # Create or coerce a protobuf request object.
        # - Quick check: If we got a request object, we should *not* have
        #   gotten any keyword arguments that map to the request.
        flattened_params = [parent, semantic_governance_policy, semantic_governance_policy_id]
        has_flattened_params = len([param for param in flattened_params if param is not None]) > 0
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        # - Use the request object if provided (there's no risk of modifying the input as
        #   there are no flattened fields), or create one.
        if not isinstance(request, semantic_governance_policy_service.CreateSemanticGovernancePolicyRequest):
            request = semantic_governance_policy_service.CreateSemanticGovernancePolicyRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent
        if semantic_governance_policy is not None:
            request.semantic_governance_policy = semantic_governance_policy
        if semantic_governance_policy_id is not None:
            request.semantic_governance_policy_id = semantic_governance_policy_id

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._client._transport._wrapped_methods[self._client._transport.create_semantic_governance_policy]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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
            semantic_governance_policy_service.SemanticGovernancePolicy,
            metadata_type=semantic_governance_policy_service.CreateSemanticGovernancePolicyOperationMetadata,
        )

        # Done; return the response.
        return response

    async def get_semantic_governance_policy(self,
            request: Optional[Union[semantic_governance_policy_service.GetSemanticGovernancePolicyRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, Union[str, bytes]]] = (),
            ) -> semantic_governance_policy_service.SemanticGovernancePolicy:
        r"""Gets a SemanticGovernancePolicy.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import aiplatform_v1beta1

            async def sample_get_semantic_governance_policy():
                # Create a client
                client = aiplatform_v1beta1.SemanticGovernancePolicyServiceAsyncClient()

                # Initialize request argument(s)
                request = aiplatform_v1beta1.GetSemanticGovernancePolicyRequest(
                    name="name_value",
                )

                # Make the request
                response = await client.get_semantic_governance_policy(request=request)

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.GetSemanticGovernancePolicyRequest, dict]]):
                The request object. Request message for
                SemanticGovernancePolicyService.GetSemanticGovernancePolicy.
            name (:class:`str`):
                Required. The name of the SemanticGovernancePolicy
                resource. Format:
                ``projects/{project}/locations/{location}/semanticGovernancePolicies/{semantic_governance_policy}``

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
            googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.SemanticGovernancePolicy:
                Represents a governance policy
                applied to a specific Agent and
                optionally a specific Tool within that
                Agent.

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
        if not isinstance(request, semantic_governance_policy_service.GetSemanticGovernancePolicyRequest):
            request = semantic_governance_policy_service.GetSemanticGovernancePolicyRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._client._transport._wrapped_methods[self._client._transport.get_semantic_governance_policy]

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

    async def list_semantic_governance_policies(self,
            request: Optional[Union[semantic_governance_policy_service.ListSemanticGovernancePoliciesRequest, dict]] = None,
            *,
            parent: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, Union[str, bytes]]] = (),
            ) -> pagers.ListSemanticGovernancePoliciesAsyncPager:
        r"""Lists SemanticGovernancePolicies in a given location.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import aiplatform_v1beta1

            async def sample_list_semantic_governance_policies():
                # Create a client
                client = aiplatform_v1beta1.SemanticGovernancePolicyServiceAsyncClient()

                # Initialize request argument(s)
                request = aiplatform_v1beta1.ListSemanticGovernancePoliciesRequest(
                    parent="parent_value",
                )

                # Make the request
                page_result = client.list_semantic_governance_policies(request=request)

                # Handle the response
                async for response in page_result:
                    print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.ListSemanticGovernancePoliciesRequest, dict]]):
                The request object. Request message for
                SemanticGovernancePolicyService.ListSemanticGovernancePolicies.
            parent (:class:`str`):
                Required. The resource name of the Location from which
                to list the SemanticGovernancePolicies. Format:
                ``projects/{project}/locations/{location}``

                This corresponds to the ``parent`` field
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
            googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.services.semantic_governance_policy_service.pagers.ListSemanticGovernancePoliciesAsyncPager:
                Response message for
                SemanticGovernancePolicyService.ListSemanticGovernancePolicies.

                Iterating over this object will yield
                results and resolve additional pages
                automatically.

        """
        # Create or coerce a protobuf request object.
        # - Quick check: If we got a request object, we should *not* have
        #   gotten any keyword arguments that map to the request.
        flattened_params = [parent]
        has_flattened_params = len([param for param in flattened_params if param is not None]) > 0
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        # - Use the request object if provided (there's no risk of modifying the input as
        #   there are no flattened fields), or create one.
        if not isinstance(request, semantic_governance_policy_service.ListSemanticGovernancePoliciesRequest):
            request = semantic_governance_policy_service.ListSemanticGovernancePoliciesRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if parent is not None:
            request.parent = parent

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._client._transport._wrapped_methods[self._client._transport.list_semantic_governance_policies]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("parent", request.parent),
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

        # This method is paged; wrap the response in a pager, which provides
        # an `__aiter__` convenience method.
        response = pagers.ListSemanticGovernancePoliciesAsyncPager(
            method=rpc,
            request=request,
            response=response,
            retry=retry,
            timeout=timeout,
            metadata=metadata,
        )

        # Done; return the response.
        return response

    async def update_semantic_governance_policy(self,
            request: Optional[Union[semantic_governance_policy_service.UpdateSemanticGovernancePolicyRequest, dict]] = None,
            *,
            semantic_governance_policy: Optional[semantic_governance_policy_service.SemanticGovernancePolicy] = None,
            update_mask: Optional[field_mask_pb2.FieldMask] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, Union[str, bytes]]] = (),
            ) -> operation_async.AsyncOperation:
        r"""Updates a SemanticGovernancePolicy.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import aiplatform_v1beta1

            async def sample_update_semantic_governance_policy():
                # Create a client
                client = aiplatform_v1beta1.SemanticGovernancePolicyServiceAsyncClient()

                # Initialize request argument(s)
                semantic_governance_policy = aiplatform_v1beta1.SemanticGovernancePolicy()
                semantic_governance_policy.natural_language_constraint = "natural_language_constraint_value"
                semantic_governance_policy.agent = "agent_value"

                request = aiplatform_v1beta1.UpdateSemanticGovernancePolicyRequest(
                    semantic_governance_policy=semantic_governance_policy,
                )

                # Make the request
                operation = client.update_semantic_governance_policy(request=request)

                print("Waiting for operation to complete...")

                response = (await operation).result()

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.UpdateSemanticGovernancePolicyRequest, dict]]):
                The request object. Request message for
                SemanticGovernancePolicyService.UpdateSemanticGovernancePolicy.
            semantic_governance_policy (:class:`googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.SemanticGovernancePolicy`):
                Required. The SemanticGovernancePolicy to update.

                The SemanticGovernancePolicy's ``name`` field is used to
                identify the SemanticGovernancePolicy to update. Format:
                ``projects/{project}/locations/{location}/semanticGovernancePolicies/{semantic_governance_policy}``

                This corresponds to the ``semantic_governance_policy`` field
                on the ``request`` instance; if ``request`` is provided, this
                should not be set.
            update_mask (:class:`google.protobuf.field_mask_pb2.FieldMask`):
                Optional. ``update_mask`` is used to specify the fields
                to be overwritten in the SemanticGovernancePolicy
                resource by the update. The fields specified in the
                ``update_mask`` are relative to the resource, not the
                full request. A field will be overwritten if it is in
                the mask. If the mask is not present, then all fields
                that are populated in the request message will be
                overwritten. Set the ``update_mask`` to ``*`` to
                override all fields.

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

                The result type for the operation will be :class:`googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.SemanticGovernancePolicy` Represents a governance policy applied to a specific Agent and optionally
                   a specific Tool within that Agent.

        """
        # Create or coerce a protobuf request object.
        # - Quick check: If we got a request object, we should *not* have
        #   gotten any keyword arguments that map to the request.
        flattened_params = [semantic_governance_policy, update_mask]
        has_flattened_params = len([param for param in flattened_params if param is not None]) > 0
        if request is not None and has_flattened_params:
            raise ValueError("If the `request` argument is set, then none of "
                             "the individual field arguments should be set.")

        # - Use the request object if provided (there's no risk of modifying the input as
        #   there are no flattened fields), or create one.
        if not isinstance(request, semantic_governance_policy_service.UpdateSemanticGovernancePolicyRequest):
            request = semantic_governance_policy_service.UpdateSemanticGovernancePolicyRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if semantic_governance_policy is not None:
            request.semantic_governance_policy = semantic_governance_policy
        if update_mask is not None:
            request.update_mask = update_mask

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._client._transport._wrapped_methods[self._client._transport.update_semantic_governance_policy]

        # Certain fields should be provided within the metadata header;
        # add these here.
        metadata = tuple(metadata) + (
            gapic_v1.routing_header.to_grpc_metadata((
                ("semantic_governance_policy.name", request.semantic_governance_policy.name),
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
            semantic_governance_policy_service.SemanticGovernancePolicy,
            metadata_type=semantic_governance_policy_service.UpdateSemanticGovernancePolicyOperationMetadata,
        )

        # Done; return the response.
        return response

    async def delete_semantic_governance_policy(self,
            request: Optional[Union[semantic_governance_policy_service.DeleteSemanticGovernancePolicyRequest, dict]] = None,
            *,
            name: Optional[str] = None,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Union[float, object] = gapic_v1.method.DEFAULT,
            metadata: Sequence[Tuple[str, Union[str, bytes]]] = (),
            ) -> operation_async.AsyncOperation:
        r"""Deletes a SemanticGovernancePolicy.

        .. code-block:: python

            # This snippet has been automatically generated and should be regarded as a
            # code template only.
            # It will require modifications to work:
            # - It may require correct/in-range values for request initialization.
            # - It may require specifying regional endpoints when creating the service
            #   client as shown in:
            #   https://googleapis.dev/python/google-api-core/latest/client_options.html
            from googlecloudsdk.generated_clients.gapic_clients import aiplatform_v1beta1

            async def sample_delete_semantic_governance_policy():
                # Create a client
                client = aiplatform_v1beta1.SemanticGovernancePolicyServiceAsyncClient()

                # Initialize request argument(s)
                request = aiplatform_v1beta1.DeleteSemanticGovernancePolicyRequest(
                    name="name_value",
                )

                # Make the request
                operation = client.delete_semantic_governance_policy(request=request)

                print("Waiting for operation to complete...")

                response = (await operation).result()

                # Handle the response
                print(response)

        Args:
            request (Optional[Union[googlecloudsdk.generated_clients.gapic_clients.aiplatform_v1beta1.types.DeleteSemanticGovernancePolicyRequest, dict]]):
                The request object. Request message for
                SemanticGovernancePolicyService.DeleteSemanticGovernancePolicy.
            name (:class:`str`):
                Required. The name of the SemanticGovernancePolicy
                resource to be deleted. Format:
                ``projects/{project}/locations/{location}/semanticGovernancePolicies/{semantic_governance_policy}``

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

                The result type for the operation will be :class:`google.protobuf.empty_pb2.Empty` A generic empty message that you can re-use to avoid defining duplicated
                   empty messages in your APIs. A typical example is to
                   use it as the request or the response type of an API
                   method. For instance:

                      service Foo {
                         rpc Bar(google.protobuf.Empty) returns
                         (google.protobuf.Empty);

                      }

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
        if not isinstance(request, semantic_governance_policy_service.DeleteSemanticGovernancePolicyRequest):
            request = semantic_governance_policy_service.DeleteSemanticGovernancePolicyRequest(request)

        # If we have keyword arguments corresponding to fields on the
        # request, apply these.
        if name is not None:
            request.name = name

        # Wrap the RPC method; this adds retry and timeout information,
        # and friendly error handling.
        rpc = self._client._transport._wrapped_methods[self._client._transport.delete_semantic_governance_policy]

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
            empty_pb2.Empty,
            metadata_type=semantic_governance_policy_service.DeleteSemanticGovernancePolicyOperationMetadata,
        )

        # Done; return the response.
        return response

    async def __aenter__(self) -> "SemanticGovernancePolicyServiceAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.transport.close()

DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(gapic_version=package_version.__version__)

if hasattr(DEFAULT_CLIENT_INFO, "protobuf_runtime_version"):   # pragma: NO COVER
    DEFAULT_CLIENT_INFO.protobuf_runtime_version = cloudsdk.google.protobuf.__version__


__all__ = (
    "SemanticGovernancePolicyServiceAsyncClient",
)
