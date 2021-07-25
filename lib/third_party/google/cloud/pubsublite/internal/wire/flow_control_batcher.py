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

from typing import List, Optional

from google.cloud.pubsublite_v1 import FlowControlRequest, SequencedMessage

_EXPEDITE_BATCH_REQUEST_RATIO = 0.5
_MAX_INT64 = 0x7FFFFFFFFFFFFFFF


class _AggregateRequest:
    request: FlowControlRequest

    def __init__(self):
        self.request = FlowControlRequest()

    def __add__(self, other: FlowControlRequest):
        self.request.allowed_bytes += other.allowed_bytes
        self.request.allowed_bytes = min(self.request.allowed_bytes, _MAX_INT64)
        self.request.allowed_messages += other.allowed_messages
        self.request.allowed_messages = min(self.request.allowed_messages, _MAX_INT64)
        return self


def _exceeds_expedite_ratio(pending: int, client: int):
    if client <= 0:
        return False
    return (pending / client) >= _EXPEDITE_BATCH_REQUEST_RATIO


def _to_optional(req: FlowControlRequest) -> Optional[FlowControlRequest]:
    if req.allowed_messages == 0 and req.allowed_bytes == 0:
        return None
    return req


class FlowControlBatcher:
    _client_tokens: _AggregateRequest
    _pending_tokens: _AggregateRequest

    def __init__(self):
        self._client_tokens = _AggregateRequest()
        self._pending_tokens = _AggregateRequest()

    def add(self, request: FlowControlRequest):
        self._client_tokens += request
        self._pending_tokens += request

    def on_messages(self, messages: List[SequencedMessage]):
        byte_size = sum(message.size_bytes for message in messages)
        self._client_tokens += FlowControlRequest(
            allowed_bytes=-byte_size, allowed_messages=-len(messages)
        )

    def request_for_restart(self) -> Optional[FlowControlRequest]:
        self._pending_tokens = _AggregateRequest()
        return _to_optional(self._client_tokens.request)

    def release_pending_request(self) -> Optional[FlowControlRequest]:
        request = self._pending_tokens.request
        self._pending_tokens = _AggregateRequest()
        return _to_optional(request)

    def should_expedite(self):
        pending_request = self._pending_tokens.request
        client_request = self._client_tokens.request
        if _exceeds_expedite_ratio(
            pending_request.allowed_bytes, client_request.allowed_bytes
        ):
            return True
        if _exceeds_expedite_ratio(
            pending_request.allowed_messages, client_request.allowed_messages
        ):
            return True
        return False
