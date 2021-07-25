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
from typing import Optional, List, Iterable

import logging

from google.cloud.pubsublite.internal.wait_ignore_cancelled import wait_ignore_errors
from google.cloud.pubsublite.internal.wire.committer import Committer
from google.cloud.pubsublite.internal.wire.retrying_connection import (
    RetryingConnection,
    ConnectionFactory,
)
from google.api_core.exceptions import FailedPrecondition, GoogleAPICallError
from google.cloud.pubsublite.internal.wire.connection_reinitializer import (
    ConnectionReinitializer,
)
from google.cloud.pubsublite.internal.wire.connection import Connection
from google.cloud.pubsublite.internal.wire.serial_batcher import (
    SerialBatcher,
    BatchTester,
)
from google.cloud.pubsublite_v1 import Cursor
from google.cloud.pubsublite_v1.types import (
    StreamingCommitCursorRequest,
    StreamingCommitCursorResponse,
    InitialCommitCursorRequest,
)
from google.cloud.pubsublite.internal.wire.work_item import WorkItem


_LOGGER = logging.getLogger(__name__)


class CommitterImpl(
    Committer,
    ConnectionReinitializer[
        StreamingCommitCursorRequest, StreamingCommitCursorResponse
    ],
    BatchTester[Cursor],
):
    _initial: InitialCommitCursorRequest
    _flush_seconds: float
    _connection: RetryingConnection[
        StreamingCommitCursorRequest, StreamingCommitCursorResponse
    ]

    _batcher: SerialBatcher[Cursor, None]

    _outstanding_commits: List[List[WorkItem[Cursor, None]]]

    _receiver: Optional[asyncio.Future]
    _flusher: Optional[asyncio.Future]

    def __init__(
        self,
        initial: InitialCommitCursorRequest,
        flush_seconds: float,
        factory: ConnectionFactory[
            StreamingCommitCursorRequest, StreamingCommitCursorResponse
        ],
    ):
        self._initial = initial
        self._flush_seconds = flush_seconds
        self._connection = RetryingConnection(factory, self)
        self._batcher = SerialBatcher(self)
        self._outstanding_commits = []
        self._receiver = None
        self._flusher = None

    async def __aenter__(self):
        await self._connection.__aenter__()
        return self

    def _start_loopers(self):
        assert self._receiver is None
        assert self._flusher is None
        self._receiver = asyncio.ensure_future(self._receive_loop())
        self._flusher = asyncio.ensure_future(self._flush_loop())

    async def _stop_loopers(self):
        if self._receiver:
            self._receiver.cancel()
            await wait_ignore_errors(self._receiver)
            self._receiver = None
        if self._flusher:
            self._flusher.cancel()
            await wait_ignore_errors(self._flusher)
            self._flusher = None

    def _handle_response(self, response: StreamingCommitCursorResponse):
        if "commit" not in response:
            self._connection.fail(
                FailedPrecondition(
                    "Received an invalid subsequent response on the commit stream."
                )
            )
        if response.commit.acknowledged_commits > len(self._outstanding_commits):
            self._connection.fail(
                FailedPrecondition(
                    "Received a commit response on the stream with no outstanding commits."
                )
            )
        for _ in range(response.commit.acknowledged_commits):
            batch = self._outstanding_commits.pop(0)
            for item in batch:
                item.response_future.set_result(None)

    async def _receive_loop(self):
        while True:
            response = await self._connection.read()
            self._handle_response(response)

    async def _flush_loop(self):
        while True:
            await asyncio.sleep(self._flush_seconds)
            await self._flush()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._stop_loopers()
        if self._connection.error():
            self._fail_if_retrying_failed()
        else:
            await self._flush()
        await self._connection.__aexit__(exc_type, exc_val, exc_tb)

    def _fail_if_retrying_failed(self):
        if self._connection.error():
            for batch in self._outstanding_commits:
                for item in batch:
                    item.response_future.set_exception(self._connection.error())

    async def _flush(self):
        batch = self._batcher.flush()
        if not batch:
            return
        self._outstanding_commits.append(batch)
        req = StreamingCommitCursorRequest()
        req.commit.cursor = batch[-1].request
        try:
            await self._connection.write(req)
        except GoogleAPICallError as e:
            _LOGGER.debug(f"Failed commit on stream: {e}")
            self._fail_if_retrying_failed()

    async def commit(self, cursor: Cursor) -> None:
        future = self._batcher.add(cursor)
        if self._batcher.should_flush():
            # always returns false currently, here in case this changes in the future.
            await self._flush()
        await future

    async def reinitialize(
        self,
        connection: Connection[
            StreamingCommitCursorRequest, StreamingCommitCursorResponse
        ],
    ):
        await self._stop_loopers()
        await connection.write(StreamingCommitCursorRequest(initial=self._initial))
        response = await connection.read()
        if "initial" not in response:
            self._connection.fail(
                FailedPrecondition(
                    "Received an invalid initial response on the publish stream."
                )
            )
        if self._outstanding_commits:
            # Roll up outstanding commits
            rollup: List[WorkItem[Cursor, None]] = []
            for batch in self._outstanding_commits:
                for item in batch:
                    rollup.append(item)
            self._outstanding_commits = [rollup]
            req = StreamingCommitCursorRequest()
            req.commit.cursor = rollup[-1].request
            await connection.write(req)
        self._start_loopers()

    def test(self, requests: Iterable[Cursor]) -> bool:
        # There is no bound on the number of outstanding cursors.
        return False
