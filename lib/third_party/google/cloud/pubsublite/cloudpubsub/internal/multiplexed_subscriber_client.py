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

from concurrent.futures.thread import ThreadPoolExecutor
from typing import Union, Optional, Set

from google.cloud.pubsub_v1.subscriber.futures import StreamingPullFuture

from google.cloud.pubsublite.cloudpubsub.internal.client_multiplexer import (
    ClientMultiplexer,
)
from google.cloud.pubsublite.cloudpubsub.internal.single_subscriber import (
    AsyncSubscriberFactory,
)
from google.cloud.pubsublite.cloudpubsub.internal.subscriber_impl import SubscriberImpl
from google.cloud.pubsublite.cloudpubsub.subscriber_client_interface import (
    SubscriberClientInterface,
    MessageCallback,
)
from google.cloud.pubsublite.types import (
    SubscriptionPath,
    FlowControlSettings,
    Partition,
)
from overrides import overrides


class MultiplexedSubscriberClient(SubscriberClientInterface):
    _executor: ThreadPoolExecutor
    _underlying_factory: AsyncSubscriberFactory

    _multiplexer: ClientMultiplexer[SubscriptionPath, StreamingPullFuture]

    def __init__(
        self, executor: ThreadPoolExecutor, underlying_factory: AsyncSubscriberFactory
    ):
        self._executor = executor
        self._underlying_factory = underlying_factory

        def cancel_streaming_pull_future(fut: StreamingPullFuture):
            try:
                fut.cancel()
                fut.result()
            except:  # noqa: E722
                pass

        self._multiplexer = ClientMultiplexer(cancel_streaming_pull_future)

    @overrides
    def subscribe(
        self,
        subscription: Union[SubscriptionPath, str],
        callback: MessageCallback,
        per_partition_flow_control_settings: FlowControlSettings,
        fixed_partitions: Optional[Set[Partition]] = None,
    ) -> StreamingPullFuture:
        if isinstance(subscription, str):
            subscription = SubscriptionPath.parse(subscription)

        def create_and_open():
            underlying = self._underlying_factory(
                subscription, fixed_partitions, per_partition_flow_control_settings
            )
            subscriber = SubscriberImpl(underlying, callback, self._executor)
            future = StreamingPullFuture(subscriber)
            subscriber.__enter__()
            return future

        future = self._multiplexer.create_or_fail(subscription, create_and_open)
        future.add_done_callback(
            lambda fut: self._multiplexer.try_erase(subscription, future)
        )
        return future

    @overrides
    def __enter__(self):
        self._executor.__enter__()
        self._multiplexer.__enter__()
        return self

    @overrides
    def __exit__(self, exc_type, exc_value, traceback):
        self._multiplexer.__exit__(exc_type, exc_value, traceback)
        self._executor.__exit__(exc_type, exc_value, traceback)
