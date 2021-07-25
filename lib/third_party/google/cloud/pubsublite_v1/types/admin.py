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

import proto  # type: ignore


from google.cloud.pubsublite_v1.types import common
from google.protobuf import field_mask_pb2 as field_mask  # type: ignore


__protobuf__ = proto.module(
    package="google.cloud.pubsublite.v1",
    manifest={
        "CreateTopicRequest",
        "GetTopicRequest",
        "GetTopicPartitionsRequest",
        "TopicPartitions",
        "ListTopicsRequest",
        "ListTopicsResponse",
        "UpdateTopicRequest",
        "DeleteTopicRequest",
        "ListTopicSubscriptionsRequest",
        "ListTopicSubscriptionsResponse",
        "CreateSubscriptionRequest",
        "GetSubscriptionRequest",
        "ListSubscriptionsRequest",
        "ListSubscriptionsResponse",
        "UpdateSubscriptionRequest",
        "DeleteSubscriptionRequest",
    },
)


class CreateTopicRequest(proto.Message):
    r"""Request for CreateTopic.

    Attributes:
        parent (str):
            Required. The parent location in which to create the topic.
            Structured like
            ``projects/{project_number}/locations/{location}``.
        topic (google.cloud.pubsublite_v1.types.Topic):
            Required. Configuration of the topic to create. Its ``name``
            field is ignored.
        topic_id (str):
            Required. The ID to use for the topic, which will become the
            final component of the topic's name.

            This value is structured like: ``my-topic-name``.
    """

    parent = proto.Field(proto.STRING, number=1)

    topic = proto.Field(proto.MESSAGE, number=2, message=common.Topic,)

    topic_id = proto.Field(proto.STRING, number=3)


class GetTopicRequest(proto.Message):
    r"""Request for GetTopic.

    Attributes:
        name (str):
            Required. The name of the topic whose
            configuration to return.
    """

    name = proto.Field(proto.STRING, number=1)


class GetTopicPartitionsRequest(proto.Message):
    r"""Request for GetTopicPartitions.

    Attributes:
        name (str):
            Required. The topic whose partition
            information to return.
    """

    name = proto.Field(proto.STRING, number=1)


class TopicPartitions(proto.Message):
    r"""Response for GetTopicPartitions.

    Attributes:
        partition_count (int):
            The number of partitions in the topic.
    """

    partition_count = proto.Field(proto.INT64, number=1)


class ListTopicsRequest(proto.Message):
    r"""Request for ListTopics.

    Attributes:
        parent (str):
            Required. The parent whose topics are to be listed.
            Structured like
            ``projects/{project_number}/locations/{location}``.
        page_size (int):
            The maximum number of topics to return. The
            service may return fewer than this value.
            If unset or zero, all topics for the parent will
            be returned.
        page_token (str):
            A page token, received from a previous ``ListTopics`` call.
            Provide this to retrieve the subsequent page.

            When paginating, all other parameters provided to
            ``ListTopics`` must match the call that provided the page
            token.
    """

    parent = proto.Field(proto.STRING, number=1)

    page_size = proto.Field(proto.INT32, number=2)

    page_token = proto.Field(proto.STRING, number=3)


class ListTopicsResponse(proto.Message):
    r"""Response for ListTopics.

    Attributes:
        topics (Sequence[google.cloud.pubsublite_v1.types.Topic]):
            The list of topic in the requested parent.
            The order of the topics is unspecified.
        next_page_token (str):
            A token that can be sent as ``page_token`` to retrieve the
            next page of results. If this field is omitted, there are no
            more results.
    """

    @property
    def raw_page(self):
        return self

    topics = proto.RepeatedField(proto.MESSAGE, number=1, message=common.Topic,)

    next_page_token = proto.Field(proto.STRING, number=2)


class UpdateTopicRequest(proto.Message):
    r"""Request for UpdateTopic.

    Attributes:
        topic (google.cloud.pubsublite_v1.types.Topic):
            Required. The topic to update. Its ``name`` field must be
            populated.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. A mask specifying the topic fields
            to change.
    """

    topic = proto.Field(proto.MESSAGE, number=1, message=common.Topic,)

    update_mask = proto.Field(proto.MESSAGE, number=2, message=field_mask.FieldMask,)


class DeleteTopicRequest(proto.Message):
    r"""Request for DeleteTopic.

    Attributes:
        name (str):
            Required. The name of the topic to delete.
    """

    name = proto.Field(proto.STRING, number=1)


class ListTopicSubscriptionsRequest(proto.Message):
    r"""Request for ListTopicSubscriptions.

    Attributes:
        name (str):
            Required. The name of the topic whose
            subscriptions to list.
        page_size (int):
            The maximum number of subscriptions to
            return. The service may return fewer than this
            value. If unset or zero, all subscriptions for
            the given topic will be returned.
        page_token (str):
            A page token, received from a previous
            ``ListTopicSubscriptions`` call. Provide this to retrieve
            the subsequent page.

            When paginating, all other parameters provided to
            ``ListTopicSubscriptions`` must match the call that provided
            the page token.
    """

    name = proto.Field(proto.STRING, number=1)

    page_size = proto.Field(proto.INT32, number=2)

    page_token = proto.Field(proto.STRING, number=3)


class ListTopicSubscriptionsResponse(proto.Message):
    r"""Response for ListTopicSubscriptions.

    Attributes:
        subscriptions (Sequence[str]):
            The names of subscriptions attached to the
            topic. The order of the subscriptions is
            unspecified.
        next_page_token (str):
            A token that can be sent as ``page_token`` to retrieve the
            next page of results. If this field is omitted, there are no
            more results.
    """

    @property
    def raw_page(self):
        return self

    subscriptions = proto.RepeatedField(proto.STRING, number=1)

    next_page_token = proto.Field(proto.STRING, number=2)


class CreateSubscriptionRequest(proto.Message):
    r"""Request for CreateSubscription.

    Attributes:
        parent (str):
            Required. The parent location in which to create the
            subscription. Structured like
            ``projects/{project_number}/locations/{location}``.
        subscription (google.cloud.pubsublite_v1.types.Subscription):
            Required. Configuration of the subscription to create. Its
            ``name`` field is ignored.
        subscription_id (str):
            Required. The ID to use for the subscription, which will
            become the final component of the subscription's name.

            This value is structured like: ``my-sub-name``.
        skip_backlog (bool):
            If true, the newly created subscription will
            only receive messages published after the
            subscription was created. Otherwise, the entire
            message backlog will be received on the
            subscription. Defaults to false.
    """

    parent = proto.Field(proto.STRING, number=1)

    subscription = proto.Field(proto.MESSAGE, number=2, message=common.Subscription,)

    subscription_id = proto.Field(proto.STRING, number=3)

    skip_backlog = proto.Field(proto.BOOL, number=4)


class GetSubscriptionRequest(proto.Message):
    r"""Request for GetSubscription.

    Attributes:
        name (str):
            Required. The name of the subscription whose
            configuration to return.
    """

    name = proto.Field(proto.STRING, number=1)


class ListSubscriptionsRequest(proto.Message):
    r"""Request for ListSubscriptions.

    Attributes:
        parent (str):
            Required. The parent whose subscriptions are to be listed.
            Structured like
            ``projects/{project_number}/locations/{location}``.
        page_size (int):
            The maximum number of subscriptions to
            return. The service may return fewer than this
            value. If unset or zero, all subscriptions for
            the parent will be returned.
        page_token (str):
            A page token, received from a previous ``ListSubscriptions``
            call. Provide this to retrieve the subsequent page.

            When paginating, all other parameters provided to
            ``ListSubscriptions`` must match the call that provided the
            page token.
    """

    parent = proto.Field(proto.STRING, number=1)

    page_size = proto.Field(proto.INT32, number=2)

    page_token = proto.Field(proto.STRING, number=3)


class ListSubscriptionsResponse(proto.Message):
    r"""Response for ListSubscriptions.

    Attributes:
        subscriptions (Sequence[google.cloud.pubsublite_v1.types.Subscription]):
            The list of subscriptions in the requested
            parent. The order of the subscriptions is
            unspecified.
        next_page_token (str):
            A token that can be sent as ``page_token`` to retrieve the
            next page of results. If this field is omitted, there are no
            more results.
    """

    @property
    def raw_page(self):
        return self

    subscriptions = proto.RepeatedField(
        proto.MESSAGE, number=1, message=common.Subscription,
    )

    next_page_token = proto.Field(proto.STRING, number=2)


class UpdateSubscriptionRequest(proto.Message):
    r"""Request for UpdateSubscription.

    Attributes:
        subscription (google.cloud.pubsublite_v1.types.Subscription):
            Required. The subscription to update. Its ``name`` field
            must be populated. Topic field must not be populated.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. A mask specifying the subscription
            fields to change.
    """

    subscription = proto.Field(proto.MESSAGE, number=1, message=common.Subscription,)

    update_mask = proto.Field(proto.MESSAGE, number=2, message=field_mask.FieldMask,)


class DeleteSubscriptionRequest(proto.Message):
    r"""Request for DeleteSubscription.

    Attributes:
        name (str):
            Required. The name of the subscription to
            delete.
    """

    name = proto.Field(proto.STRING, number=1)


__all__ = tuple(sorted(__protobuf__.manifest))
