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
from asyncio import Future

from typing import Optional
from google.api_core.exceptions import GoogleAPICallError, Cancelled
from google.cloud.pubsublite.internal.status_codes import is_retryable
from google.cloud.pubsublite.internal.wait_ignore_cancelled import wait_ignore_errors
from google.cloud.pubsublite.internal.wire.connection_reinitializer import (
    ConnectionReinitializer,
)
from google.cloud.pubsublite.internal.wire.connection import (
    Connection,
    Request,
    Response,
    ConnectionFactory,
)
from google.cloud.pubsublite.internal.wire.work_item import WorkItem
from google.cloud.pubsublite.internal.wire.permanent_failable import PermanentFailable

_MIN_BACKOFF_SECS = 0.01
_MAX_BACKOFF_SECS = 10


class RetryingConnection(Connection[Request, Response], PermanentFailable):
    """A connection which performs retries on an underlying stream when experiencing retryable errors."""

    _connection_factory: ConnectionFactory[Request, Response]
    _reinitializer: ConnectionReinitializer[Request, Response]
    _initialized_once: asyncio.Event

    _loop_task: asyncio.Future

    _write_queue: "asyncio.Queue[WorkItem[Request, None]]"
    _read_queue: "asyncio.Queue[Response]"

    def __init__(
        self,
        connection_factory: ConnectionFactory[Request, Response],
        reinitializer: ConnectionReinitializer[Request, Response],
    ):
        super().__init__()
        self._connection_factory = connection_factory
        self._reinitializer = reinitializer
        self._initialized_once = asyncio.Event()
        self._write_queue = asyncio.Queue(maxsize=1)
        self._read_queue = asyncio.Queue(maxsize=1)

    async def __aenter__(self):
        self._loop_task = asyncio.ensure_future(self._run_loop())
        await self.await_unless_failed(self._initialized_once.wait())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.fail(Cancelled("Connection shutting down."))

    async def write(self, request: Request) -> None:
        item = WorkItem(request)
        await self.await_unless_failed(self._write_queue.put(item))
        return await self.await_unless_failed(item.response_future)

    async def read(self) -> Response:
        return await self.await_unless_failed(self._read_queue.get())

    async def _run_loop(self):
        """
    Processes actions on this connection and handles retries until cancelled.
    """
        last_failure: Optional[GoogleAPICallError] = None
        try:
            bad_retries = 0
            while True:
                try:
                    conn_fut = self._connection_factory.new()
                    async with (await conn_fut) as connection:
                        # Needs to happen prior to reinitialization to clear outstanding waiters.
                        if last_failure is not None:
                            while not self._write_queue.empty():
                                self._write_queue.get_nowait().response_future.set_exception(
                                    last_failure
                                )
                        self._read_queue = asyncio.Queue(maxsize=1)
                        self._write_queue = asyncio.Queue(maxsize=1)
                        await self._reinitializer.reinitialize(connection)
                        self._initialized_once.set()
                        bad_retries = 0
                        await self._loop_connection(connection)
                except GoogleAPICallError as e:
                    last_failure = e
                    if not is_retryable(e):
                        self.fail(e)
                        return
                    await asyncio.sleep(
                        min(_MAX_BACKOFF_SECS, _MIN_BACKOFF_SECS * (2 ** bad_retries))
                    )
                    bad_retries += 1

        except asyncio.CancelledError:
            return
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(e)

    async def _loop_connection(self, connection: Connection[Request, Response]):
        read_task: "Future[Response]" = asyncio.ensure_future(connection.read())
        write_task: "Future[WorkItem[Request]]" = asyncio.ensure_future(
            self._write_queue.get()
        )
        try:
            while True:
                done, _ = await asyncio.wait(
                    [write_task, read_task], return_when=asyncio.FIRST_COMPLETED
                )
                if write_task in done:
                    await self._handle_write(connection, await write_task)
                    write_task = asyncio.ensure_future(self._write_queue.get())
                if read_task in done:
                    await self._read_queue.put(await read_task)
                    read_task = asyncio.ensure_future(connection.read())
        finally:
            read_task.cancel()
            write_task.cancel()
            await wait_ignore_errors(read_task)
            await wait_ignore_errors(write_task)

    @staticmethod
    async def _handle_write(
        connection: Connection[Request, Response], to_write: WorkItem[Request, Response]
    ):
        try:
            await connection.write(to_write.request)
            to_write.response_future.set_result(None)
        except GoogleAPICallError as e:
            to_write.response_future.set_exception(e)
            raise e
