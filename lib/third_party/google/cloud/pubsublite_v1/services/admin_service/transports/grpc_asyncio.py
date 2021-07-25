# -*- coding: utf-8 -*-

# Copyright 2020 Google LLC
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

import warnings
from typing import Awaitable, Callable, Dict, Optional, Sequence, Tuple

from google.api_core import gapic_v1  # type: ignore
from google.api_core import grpc_helpers_async  # type: ignore
from google import auth  # type: ignore
from google.auth import credentials  # type: ignore
from google.auth.transport.grpc import SslCredentials  # type: ignore

import grpc  # type: ignore
from grpc.experimental import aio  # type: ignore

from google.cloud.pubsublite_v1.types import admin
from google.cloud.pubsublite_v1.types import common
from google.protobuf import empty_pb2 as empty  # type: ignore

from .base import AdminServiceTransport, DEFAULT_CLIENT_INFO
from .grpc import AdminServiceGrpcTransport


class AdminServiceGrpcAsyncIOTransport(AdminServiceTransport):
    """gRPC AsyncIO backend transport for AdminService.

    The service that a client application uses to manage topics
    and subscriptions, such creating, listing, and deleting topics
    and subscriptions.

    This class defines the same methods as the primary client, so the
    primary client can load the underlying transport implementation
    and call it.

    It sends protocol buffers over the wire using gRPC (which is built on
    top of HTTP/2); the ``grpcio`` package must be installed.
    """

    _grpc_channel: aio.Channel
    _stubs: Dict[str, Callable] = {}

    @classmethod
    def create_channel(
        cls,
        host: str = "pubsublite.googleapis.com",
        credentials: credentials.Credentials = None,
        credentials_file: Optional[str] = None,
        scopes: Optional[Sequence[str]] = None,
        quota_project_id: Optional[str] = None,
        **kwargs,
    ) -> aio.Channel:
        """Create and return a gRPC AsyncIO channel object.
        Args:
            host (Optional[str]): The host for the channel to use.
            credentials (Optional[~.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify this application to the service. If
                none are specified, the client will attempt to ascertain
                the credentials from the environment.
            credentials_file (Optional[str]): A file with credentials that can
                be loaded with :func:`google.auth.load_credentials_from_file`.
                This argument is ignored if ``channel`` is provided.
            scopes (Optional[Sequence[str]]): A optional list of scopes needed for this
                service. These are only used when credentials are not specified and
                are passed to :func:`google.auth.default`.
            quota_project_id (Optional[str]): An optional project to use for billing
                and quota.
            kwargs (Optional[dict]): Keyword arguments, which are passed to the
                channel creation.
        Returns:
            aio.Channel: A gRPC AsyncIO channel object.
        """
        scopes = scopes or cls.AUTH_SCOPES
        return grpc_helpers_async.create_channel(
            host,
            credentials=credentials,
            credentials_file=credentials_file,
            scopes=scopes,
            quota_project_id=quota_project_id,
            **kwargs,
        )

    def __init__(
        self,
        *,
        host: str = "pubsublite.googleapis.com",
        credentials: credentials.Credentials = None,
        credentials_file: Optional[str] = None,
        scopes: Optional[Sequence[str]] = None,
        channel: aio.Channel = None,
        api_mtls_endpoint: str = None,
        client_cert_source: Callable[[], Tuple[bytes, bytes]] = None,
        ssl_channel_credentials: grpc.ChannelCredentials = None,
        client_cert_source_for_mtls: Callable[[], Tuple[bytes, bytes]] = None,
        quota_project_id=None,
        client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
    ) -> None:
        """Instantiate the transport.

        Args:
            host (Optional[str]): The hostname to connect to.
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.
                This argument is ignored if ``channel`` is provided.
            credentials_file (Optional[str]): A file with credentials that can
                be loaded with :func:`google.auth.load_credentials_from_file`.
                This argument is ignored if ``channel`` is provided.
            scopes (Optional[Sequence[str]]): A optional list of scopes needed for this
                service. These are only used when credentials are not specified and
                are passed to :func:`google.auth.default`.
            channel (Optional[aio.Channel]): A ``Channel`` instance through
                which to make calls.
            api_mtls_endpoint (Optional[str]): Deprecated. The mutual TLS endpoint.
                If provided, it overrides the ``host`` argument and tries to create
                a mutual TLS channel with client SSL credentials from
                ``client_cert_source`` or applicatin default SSL credentials.
            client_cert_source (Optional[Callable[[], Tuple[bytes, bytes]]]):
                Deprecated. A callback to provide client SSL certificate bytes and
                private key bytes, both in PEM format. It is ignored if
                ``api_mtls_endpoint`` is None.
            ssl_channel_credentials (grpc.ChannelCredentials): SSL credentials
                for grpc channel. It is ignored if ``channel`` is provided.
            client_cert_source_for_mtls (Optional[Callable[[], Tuple[bytes, bytes]]]):
                A callback to provide client certificate bytes and private key bytes,
                both in PEM format. It is used to configure mutual TLS channel. It is
                ignored if ``channel`` or ``ssl_channel_credentials`` is provided.
            quota_project_id (Optional[str]): An optional project to use for billing
                and quota.
            client_info (google.api_core.gapic_v1.client_info.ClientInfo):
                The client info used to send a user-agent string along with
                API requests. If ``None``, then default info will be used.
                Generally, you only need to set this if you're developing
                your own client library.

        Raises:
            google.auth.exceptions.MutualTlsChannelError: If mutual TLS transport
              creation failed for any reason.
          google.api_core.exceptions.DuplicateCredentialArgs: If both ``credentials``
              and ``credentials_file`` are passed.
        """
        self._grpc_channel = None
        self._ssl_channel_credentials = ssl_channel_credentials
        self._stubs: Dict[str, Callable] = {}

        if api_mtls_endpoint:
            warnings.warn("api_mtls_endpoint is deprecated", DeprecationWarning)
        if client_cert_source:
            warnings.warn("client_cert_source is deprecated", DeprecationWarning)

        if channel:
            # Ignore credentials if a channel was passed.
            credentials = False
            # If a channel was explicitly provided, set it.
            self._grpc_channel = channel
            self._ssl_channel_credentials = None

        else:
            if api_mtls_endpoint:
                host = api_mtls_endpoint

                # Create SSL credentials with client_cert_source or application
                # default SSL credentials.
                if client_cert_source:
                    cert, key = client_cert_source()
                    self._ssl_channel_credentials = grpc.ssl_channel_credentials(
                        certificate_chain=cert, private_key=key
                    )
                else:
                    self._ssl_channel_credentials = SslCredentials().ssl_credentials

            else:
                if client_cert_source_for_mtls and not ssl_channel_credentials:
                    cert, key = client_cert_source_for_mtls()
                    self._ssl_channel_credentials = grpc.ssl_channel_credentials(
                        certificate_chain=cert, private_key=key
                    )

        # The base transport sets the host, credentials and scopes
        super().__init__(
            host=host,
            credentials=credentials,
            credentials_file=credentials_file,
            scopes=scopes,
            quota_project_id=quota_project_id,
            client_info=client_info,
        )

        if not self._grpc_channel:
            self._grpc_channel = type(self).create_channel(
                self._host,
                credentials=self._credentials,
                credentials_file=credentials_file,
                scopes=self._scopes,
                ssl_credentials=self._ssl_channel_credentials,
                quota_project_id=quota_project_id,
                options=[
                    ("grpc.max_send_message_length", -1),
                    ("grpc.max_receive_message_length", -1),
                ],
            )

        # Wrap messages. This must be done after self._grpc_channel exists
        self._prep_wrapped_messages(client_info)

    @property
    def grpc_channel(self) -> aio.Channel:
        """Create the channel designed to connect to this service.

        This property caches on the instance; repeated calls return
        the same channel.
        """
        # Return the channel from cache.
        return self._grpc_channel

    @property
    def create_topic(
        self,
    ) -> Callable[[admin.CreateTopicRequest], Awaitable[common.Topic]]:
        r"""Return a callable for the create topic method over gRPC.

        Creates a new topic.

        Returns:
            Callable[[~.CreateTopicRequest],
                    Awaitable[~.Topic]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "create_topic" not in self._stubs:
            self._stubs["create_topic"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/CreateTopic",
                request_serializer=admin.CreateTopicRequest.serialize,
                response_deserializer=common.Topic.deserialize,
            )
        return self._stubs["create_topic"]

    @property
    def get_topic(self) -> Callable[[admin.GetTopicRequest], Awaitable[common.Topic]]:
        r"""Return a callable for the get topic method over gRPC.

        Returns the topic configuration.

        Returns:
            Callable[[~.GetTopicRequest],
                    Awaitable[~.Topic]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "get_topic" not in self._stubs:
            self._stubs["get_topic"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/GetTopic",
                request_serializer=admin.GetTopicRequest.serialize,
                response_deserializer=common.Topic.deserialize,
            )
        return self._stubs["get_topic"]

    @property
    def get_topic_partitions(
        self,
    ) -> Callable[[admin.GetTopicPartitionsRequest], Awaitable[admin.TopicPartitions]]:
        r"""Return a callable for the get topic partitions method over gRPC.

        Returns the partition information for the requested
        topic.

        Returns:
            Callable[[~.GetTopicPartitionsRequest],
                    Awaitable[~.TopicPartitions]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "get_topic_partitions" not in self._stubs:
            self._stubs["get_topic_partitions"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/GetTopicPartitions",
                request_serializer=admin.GetTopicPartitionsRequest.serialize,
                response_deserializer=admin.TopicPartitions.deserialize,
            )
        return self._stubs["get_topic_partitions"]

    @property
    def list_topics(
        self,
    ) -> Callable[[admin.ListTopicsRequest], Awaitable[admin.ListTopicsResponse]]:
        r"""Return a callable for the list topics method over gRPC.

        Returns the list of topics for the given project.

        Returns:
            Callable[[~.ListTopicsRequest],
                    Awaitable[~.ListTopicsResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "list_topics" not in self._stubs:
            self._stubs["list_topics"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/ListTopics",
                request_serializer=admin.ListTopicsRequest.serialize,
                response_deserializer=admin.ListTopicsResponse.deserialize,
            )
        return self._stubs["list_topics"]

    @property
    def update_topic(
        self,
    ) -> Callable[[admin.UpdateTopicRequest], Awaitable[common.Topic]]:
        r"""Return a callable for the update topic method over gRPC.

        Updates properties of the specified topic.

        Returns:
            Callable[[~.UpdateTopicRequest],
                    Awaitable[~.Topic]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "update_topic" not in self._stubs:
            self._stubs["update_topic"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/UpdateTopic",
                request_serializer=admin.UpdateTopicRequest.serialize,
                response_deserializer=common.Topic.deserialize,
            )
        return self._stubs["update_topic"]

    @property
    def delete_topic(
        self,
    ) -> Callable[[admin.DeleteTopicRequest], Awaitable[empty.Empty]]:
        r"""Return a callable for the delete topic method over gRPC.

        Deletes the specified topic.

        Returns:
            Callable[[~.DeleteTopicRequest],
                    Awaitable[~.Empty]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "delete_topic" not in self._stubs:
            self._stubs["delete_topic"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/DeleteTopic",
                request_serializer=admin.DeleteTopicRequest.serialize,
                response_deserializer=empty.Empty.FromString,
            )
        return self._stubs["delete_topic"]

    @property
    def list_topic_subscriptions(
        self,
    ) -> Callable[
        [admin.ListTopicSubscriptionsRequest],
        Awaitable[admin.ListTopicSubscriptionsResponse],
    ]:
        r"""Return a callable for the list topic subscriptions method over gRPC.

        Lists the subscriptions attached to the specified
        topic.

        Returns:
            Callable[[~.ListTopicSubscriptionsRequest],
                    Awaitable[~.ListTopicSubscriptionsResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "list_topic_subscriptions" not in self._stubs:
            self._stubs["list_topic_subscriptions"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/ListTopicSubscriptions",
                request_serializer=admin.ListTopicSubscriptionsRequest.serialize,
                response_deserializer=admin.ListTopicSubscriptionsResponse.deserialize,
            )
        return self._stubs["list_topic_subscriptions"]

    @property
    def create_subscription(
        self,
    ) -> Callable[[admin.CreateSubscriptionRequest], Awaitable[common.Subscription]]:
        r"""Return a callable for the create subscription method over gRPC.

        Creates a new subscription.

        Returns:
            Callable[[~.CreateSubscriptionRequest],
                    Awaitable[~.Subscription]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "create_subscription" not in self._stubs:
            self._stubs["create_subscription"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/CreateSubscription",
                request_serializer=admin.CreateSubscriptionRequest.serialize,
                response_deserializer=common.Subscription.deserialize,
            )
        return self._stubs["create_subscription"]

    @property
    def get_subscription(
        self,
    ) -> Callable[[admin.GetSubscriptionRequest], Awaitable[common.Subscription]]:
        r"""Return a callable for the get subscription method over gRPC.

        Returns the subscription configuration.

        Returns:
            Callable[[~.GetSubscriptionRequest],
                    Awaitable[~.Subscription]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "get_subscription" not in self._stubs:
            self._stubs["get_subscription"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/GetSubscription",
                request_serializer=admin.GetSubscriptionRequest.serialize,
                response_deserializer=common.Subscription.deserialize,
            )
        return self._stubs["get_subscription"]

    @property
    def list_subscriptions(
        self,
    ) -> Callable[
        [admin.ListSubscriptionsRequest], Awaitable[admin.ListSubscriptionsResponse]
    ]:
        r"""Return a callable for the list subscriptions method over gRPC.

        Returns the list of subscriptions for the given
        project.

        Returns:
            Callable[[~.ListSubscriptionsRequest],
                    Awaitable[~.ListSubscriptionsResponse]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "list_subscriptions" not in self._stubs:
            self._stubs["list_subscriptions"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/ListSubscriptions",
                request_serializer=admin.ListSubscriptionsRequest.serialize,
                response_deserializer=admin.ListSubscriptionsResponse.deserialize,
            )
        return self._stubs["list_subscriptions"]

    @property
    def update_subscription(
        self,
    ) -> Callable[[admin.UpdateSubscriptionRequest], Awaitable[common.Subscription]]:
        r"""Return a callable for the update subscription method over gRPC.

        Updates properties of the specified subscription.

        Returns:
            Callable[[~.UpdateSubscriptionRequest],
                    Awaitable[~.Subscription]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "update_subscription" not in self._stubs:
            self._stubs["update_subscription"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/UpdateSubscription",
                request_serializer=admin.UpdateSubscriptionRequest.serialize,
                response_deserializer=common.Subscription.deserialize,
            )
        return self._stubs["update_subscription"]

    @property
    def delete_subscription(
        self,
    ) -> Callable[[admin.DeleteSubscriptionRequest], Awaitable[empty.Empty]]:
        r"""Return a callable for the delete subscription method over gRPC.

        Deletes the specified subscription.

        Returns:
            Callable[[~.DeleteSubscriptionRequest],
                    Awaitable[~.Empty]]:
                A function that, when called, will call the underlying RPC
                on the server.
        """
        # Generate a "stub function" on-the-fly which will actually make
        # the request.
        # gRPC handles serialization and deserialization, so we just need
        # to pass in the functions for each.
        if "delete_subscription" not in self._stubs:
            self._stubs["delete_subscription"] = self.grpc_channel.unary_unary(
                "/google.cloud.pubsublite.v1.AdminService/DeleteSubscription",
                request_serializer=admin.DeleteSubscriptionRequest.serialize,
                response_deserializer=empty.Empty.FromString,
            )
        return self._stubs["delete_subscription"]


__all__ = ("AdminServiceGrpcAsyncIOTransport",)
