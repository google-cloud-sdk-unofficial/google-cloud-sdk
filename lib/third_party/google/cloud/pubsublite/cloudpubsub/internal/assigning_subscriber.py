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

from asyncio import Future, Queue, ensure_future
from typing import Callable, NamedTuple, Dict, Set, Optional

from google.cloud.pubsub_v1.subscriber.message import Message

from google.cloud.pubsublite.cloudpubsub.internal.single_subscriber import (
    AsyncSingleSubscriber,
)
from google.cloud.pubsublite.internal.wait_ignore_cancelled import wait_ignore_cancelled
from google.cloud.pubsublite.internal.wire.assigner import Assigner
from google.cloud.pubsublite.internal.wire.permanent_failable import PermanentFailable
from google.cloud.pubsublite.types import Partition

PartitionSubscriberFactory = Callable[[Partition], AsyncSingleSubscriber]


class _RunningSubscriber(NamedTuple):
    subscriber: AsyncSingleSubscriber
    poller: Future


class AssigningSingleSubscriber(AsyncSingleSubscriber, PermanentFailable):
    _assigner_factory: Callable[[], Assigner]
    _subscriber_factory: PartitionSubscriberFactory

    _subscribers: Dict[Partition, _RunningSubscriber]

    # Lazily initialized to ensure they are initialized on the thread where __aenter__ is called.
    _assigner: Optional[Assigner]
    _messages: Optional["Queue[Message]"]
    _assign_poller: Future

    def __init__(
        self,
        assigner_factory: Callable[[], Assigner],
        subscriber_factory: PartitionSubscriberFactory,
    ):
        """
        Accepts a factory for an Assigner instead of an Assigner because GRPC asyncio uses the current thread's event
        loop.
        """
        super().__init__()
        self._assigner_factory = assigner_factory
        self._assigner = None
        self._subscriber_factory = subscriber_factory
        self._subscribers = {}
        self._messages = None

    async def read(self) -> Message:
        return await self.await_unless_failed(self._messages.get())

    async def _subscribe_action(self, subscriber: AsyncSingleSubscriber):
        message = await subscriber.read()
        await self._messages.put(message)

    async def _start_subscriber(self, partition: Partition):
        new_subscriber = self._subscriber_factory(partition)
        await new_subscriber.__aenter__()
        poller = ensure_future(
            self.run_poller(lambda: self._subscribe_action(new_subscriber))
        )
        self._subscribers[partition] = _RunningSubscriber(new_subscriber, poller)

    async def _stop_subscriber(self, running: _RunningSubscriber):
        running.poller.cancel()
        await wait_ignore_cancelled(running.poller)
        await running.subscriber.__aexit__(None, None, None)

    async def _assign_action(self):
        assignment: Set[Partition] = await self._assigner.get_assignment()
        added_partitions = assignment - self._subscribers.keys()
        removed_partitions = self._subscribers.keys() - assignment
        for partition in added_partitions:
            await self._start_subscriber(partition)
        for partition in removed_partitions:
            subscriber = self._subscribers[partition]
            del self._subscribers[partition]
            await self._stop_subscriber(subscriber)

    async def __aenter__(self):
        self._messages = Queue()
        self._assigner = self._assigner_factory()
        await self._assigner.__aenter__()
        self._assign_poller = ensure_future(self.run_poller(self._assign_action))
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._assign_poller.cancel()
        await wait_ignore_cancelled(self._assign_poller)
        await self._assigner.__aexit__(exc_type, exc_value, traceback)
        for running in self._subscribers.values():
            await self._stop_subscriber(running)
        pass
