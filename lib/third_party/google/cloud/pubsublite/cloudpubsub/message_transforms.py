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

import datetime

from google.api_core.exceptions import InvalidArgument
from google.protobuf.timestamp_pb2 import Timestamp
from google.pubsub_v1 import PubsubMessage

from google.cloud.pubsublite.cloudpubsub import MessageTransformer
from google.cloud.pubsublite.types import Partition, MessageMetadata
from google.cloud.pubsublite_v1 import AttributeValues, SequencedMessage, PubSubMessage

PUBSUB_LITE_EVENT_TIME = "x-goog-pubsublite-event-time"


def encode_attribute_event_time(dt: datetime.datetime) -> str:
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts.ToJsonString()


def decode_attribute_event_time(attr: str) -> datetime.datetime:
    try:
        ts = Timestamp()
        ts.FromJsonString(attr)
        return ts.ToDatetime()
    except ValueError:
        raise InvalidArgument("Invalid value for event time attribute.")


def _parse_attributes(values: AttributeValues) -> str:
    if not len(values.values) == 1:
        raise InvalidArgument(
            "Received an unparseable message with multiple values for an attribute."
        )
    value: bytes = values.values[0]
    try:
        return value.decode("utf-8")
    except UnicodeError:
        raise InvalidArgument(
            "Received an unparseable message with a non-utf8 attribute."
        )


def add_id_to_cps_subscribe_transformer(
    partition: Partition, transformer: MessageTransformer
) -> MessageTransformer:
    def add_id_to_message(source: SequencedMessage):
        message: PubsubMessage = transformer.transform(source)
        if message.message_id:
            raise InvalidArgument(
                "Message after transforming has the message_id field set."
            )
        message.message_id = MessageMetadata(partition, source.cursor).encode()
        return message

    return MessageTransformer.of_callable(add_id_to_message)


def to_cps_subscribe_message(source: SequencedMessage) -> PubsubMessage:
    message: PubsubMessage = to_cps_publish_message(source.message)
    message.publish_time = source.publish_time
    return message


def to_cps_publish_message(source: PubSubMessage) -> PubsubMessage:
    out = PubsubMessage()
    try:
        out.ordering_key = source.key.decode("utf-8")
    except UnicodeError:
        raise InvalidArgument("Received an unparseable message with a non-utf8 key.")
    if PUBSUB_LITE_EVENT_TIME in source.attributes:
        raise InvalidArgument(
            "Special timestamp attribute exists in wire message. Unable to parse message."
        )
    out.data = source.data
    for key, values in source.attributes.items():
        out.attributes[key] = _parse_attributes(values)
    if "event_time" in source:
        out.attributes[PUBSUB_LITE_EVENT_TIME] = encode_attribute_event_time(
            source.event_time
        )
    return out


def from_cps_publish_message(source: PubsubMessage) -> PubSubMessage:
    out = PubSubMessage()
    if PUBSUB_LITE_EVENT_TIME in source.attributes:
        out.event_time = decode_attribute_event_time(
            source.attributes[PUBSUB_LITE_EVENT_TIME]
        )
    out.data = source.data
    out.key = source.ordering_key.encode("utf-8")
    for key, value in source.attributes.items():
        if key != PUBSUB_LITE_EVENT_TIME:
            out.attributes[key] = AttributeValues(values=[value.encode("utf-8")])
    return out
