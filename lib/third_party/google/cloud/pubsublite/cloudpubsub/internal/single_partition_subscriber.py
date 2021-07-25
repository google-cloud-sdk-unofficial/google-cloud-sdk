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

import asyncio
from typing import Union, Dict, NamedTuple
import queue

from google.api_core.exceptions import FailedPrecondition, GoogleAPICallError
from google.cloud.pubsub_v1.subscriber.message import Message
from google.pubsub_v1 import PubsubMessage

from google.cloud.pubsublite.internal.wait_ignore_cancelled import wait_ignore_cancelled
from google.cloud.pubsublite.types import FlowControlSettings
from google.cloud.pubsublite.cloudpubsub.internal.ack_set_tracker import AckSetTracker
from google.cloud.pubsublite.cloudpubsub.message_transformer import MessageTransformer
from google.cloud.pubsublite.cloudpubsub.nack_handler import NackHandler
from google.cloud.pubsublite.cloudpubsub.internal.single_subscriber import (
    AsyncSingleSubscriber,
)
from google.cloud.pubsublite.internal.wire.permanent_failable import PermanentFailable
from google.cloud.pubsublite.internal.wire.subscriber import Subscriber
from google.cloud.pubsublite_v1 import FlowControlRequest, SequencedMessage
from google.cloud.pubsub_v1.subscriber._protocol import requests


class _SizedMessage(NamedTuple):
    message: PubsubMessage
    size_bytes: int


class SinglePartitionSingleSubscriber(PermanentFailable, AsyncSingleSubscriber):
    _underlying: Subscriber
    _flow_control_settings: FlowControlSettings
    _ack_set_tracker: AckSetTracker
    _nack_handler: NackHandler
    _transformer: MessageTransformer

    _queue: queue.Queue
    _messages_by_offset: Dict[int, _SizedMessage]
    _looper_future: asyncio.Future

    def __init__(
        self,
        underlying: Subscriber,
        flow_control_settings: FlowControlSettings,
        ack_set_tracker: AckSetTracker,
        nack_handler: NackHandler,
        transformer: MessageTransformer,
    ):
        super().__init__()
        self._underlying = underlying
        self._flow_control_settings = flow_control_settings
        self._ack_set_tracker = ack_set_tracker
        self._nack_handler = nack_handler
        self._transformer = transformer

        self._queue = queue.Queue()
        self._messages_by_offset = {}

    async def read(self) -> Message:
        try:
            message: SequencedMessage = await self.await_unless_failed(
                self._underlying.read()
            )
            cps_message = self._transformer.transform(message)
            offset = message.cursor.offset
            self._ack_set_tracker.track(offset)
            self._messages_by_offset[offset] = _SizedMessage(
                cps_message, message.size_bytes
            )
            wrapped_message = Message(
                cps_message._pb,
                ack_id=str(offset),
                delivery_attempt=0,
                request_queue=self._queue,
            )
            return wrapped_message
        except GoogleAPICallError as e:
            self.fail(e)
            raise e

    async def _handle_ack(self, message: requests.AckRequest):
        offset = int(message.ack_id)
        await self._underlying.allow_flow(
            FlowControlRequest(
                allowed_messages=1,
                allowed_bytes=self._messages_by_offset[offset].size_bytes,
            )
        )
        del self._messages_by_offset[offset]
        try:
            await self._ack_set_tracker.ack(offset)
        except GoogleAPICallError as e:
            self.fail(e)

    def _handle_nack(self, message: requests.NackRequest):
        offset = int(message.ack_id)
        sized_message = self._messages_by_offset[offset]
        try:
            # Put the ack request back into the queue since the callback may be called from another thread.
            self._nack_handler.on_nack(
                sized_message.message,
                lambda: self._queue.put(
                    requests.AckRequest(
                        ack_id=message.ack_id,
                        byte_size=0,  # Ignored
                        time_to_ack=0,  # Ignored
                        ordering_key="",  # Ignored
                    )
                ),
            )
        except GoogleAPICallError as e:
            self.fail(e)

    async def _handle_queue_message(
        self,
        message: Union[
            requests.AckRequest,
            requests.DropRequest,
            requests.ModAckRequest,
            requests.NackRequest,
        ],
    ):
        if isinstance(message, requests.DropRequest) or isinstance(
            message, requests.ModAckRequest
        ):
            self.fail(
                FailedPrecondition(
                    "Called internal method of google.cloud.pubsub_v1.subscriber.message.Message "
                    f"Pub/Sub Lite does not support: {message}"
                )
            )
        elif isinstance(message, requests.AckRequest):
            await self._handle_ack(message)
        else:
            self._handle_nack(message)

    async def _looper(self):
        while True:
            try:
                # This is not an asyncio.Queue, and therefore we cannot do `await self._queue.get()`.
                # A blocking wait would block the event loop, this needs to be a queue.Queue for
                # compatibility with the Cloud Pub/Sub Message's requirements.
                queue_message = self._queue.get_nowait()
                await self._handle_queue_message(queue_message)
            except queue.Empty:
                await asyncio.sleep(0.1)

    async def __aenter__(self):
        await self._ack_set_tracker.__aenter__()
        await self._underlying.__aenter__()
        self._looper_future = asyncio.ensure_future(self._looper())
        await self._underlying.allow_flow(
            FlowControlRequest(
                allowed_messages=self._flow_control_settings.messages_outstanding,
                allowed_bytes=self._flow_control_settings.bytes_outstanding,
            )
        )
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._looper_future.cancel()
        await wait_ignore_cancelled(self._looper_future)
        await self._underlying.__aexit__(exc_type, exc_value, traceback)
        await self._ack_set_tracker.__aexit__(exc_type, exc_value, traceback)
