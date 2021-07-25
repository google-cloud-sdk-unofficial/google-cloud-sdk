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

from typing import Optional, List

from overrides import overrides
from google.api_core.client_options import ClientOptions
from google.auth.credentials import Credentials
from google.protobuf.field_mask_pb2 import FieldMask

from google.cloud.pubsublite.admin_client_interface import AdminClientInterface
from google.cloud.pubsublite.internal.constructable_from_service_account import (
    ConstructableFromServiceAccount,
)
from google.cloud.pubsublite.internal.endpoints import regional_endpoint
from google.cloud.pubsublite.internal.wire.admin_client_impl import AdminClientImpl
from google.cloud.pubsublite.types import (
    CloudRegion,
    SubscriptionPath,
    LocationPath,
    TopicPath,
    BacklogLocation,
)
from google.cloud.pubsublite_v1 import AdminServiceClient, Subscription, Topic


class AdminClient(AdminClientInterface, ConstructableFromServiceAccount):
    """
    An admin client for Pub/Sub Lite. Only operates on a single region.
    """

    _impl: AdminClientInterface

    def __init__(
        self,
        region: CloudRegion,
        credentials: Optional[Credentials] = None,
        transport: Optional[str] = None,
        client_options: Optional[ClientOptions] = None,
    ):
        """
        Create a new AdminClient.

        Args:
            region: The cloud region to connect to.
            credentials: The credentials to use when connecting.
            transport: The transport to use.
            client_options: The client options to use when connecting. If used, must explicitly set `api_endpoint`.
        """
        if client_options is None:
            client_options = ClientOptions(api_endpoint=regional_endpoint(region))
        self._impl = AdminClientImpl(
            AdminServiceClient(
                client_options=client_options,
                transport=transport,
                credentials=credentials,
            ),
            region,
        )

    @overrides
    def region(self) -> CloudRegion:
        return self._impl.region()

    @overrides
    def create_topic(self, topic: Topic) -> Topic:
        return self._impl.create_topic(topic)

    @overrides
    def get_topic(self, topic_path: TopicPath) -> Topic:
        return self._impl.get_topic(topic_path)

    @overrides
    def get_topic_partition_count(self, topic_path: TopicPath) -> int:
        return self._impl.get_topic_partition_count(topic_path)

    @overrides
    def list_topics(self, location_path: LocationPath) -> List[Topic]:
        return self._impl.list_topics(location_path)

    @overrides
    def update_topic(self, topic: Topic, update_mask: FieldMask) -> Topic:
        return self._impl.update_topic(topic, update_mask)

    @overrides
    def delete_topic(self, topic_path: TopicPath):
        return self._impl.delete_topic(topic_path)

    @overrides
    def list_topic_subscriptions(self, topic_path: TopicPath):
        return self._impl.list_topic_subscriptions(topic_path)

    @overrides
    def create_subscription(
        self,
        subscription: Subscription,
        starting_offset: BacklogLocation = BacklogLocation.END,
    ) -> Subscription:
        return self._impl.create_subscription(subscription, starting_offset)

    @overrides
    def get_subscription(self, subscription_path: SubscriptionPath) -> Subscription:
        return self._impl.get_subscription(subscription_path)

    @overrides
    def list_subscriptions(self, location_path: LocationPath) -> List[Subscription]:
        return self._impl.list_subscriptions(location_path)

    @overrides
    def update_subscription(
        self, subscription: Subscription, update_mask: FieldMask
    ) -> Subscription:
        return self._impl.update_subscription(subscription, update_mask)

    @overrides
    def delete_subscription(self, subscription_path: SubscriptionPath):
        return self._impl.delete_subscription(subscription_path)
