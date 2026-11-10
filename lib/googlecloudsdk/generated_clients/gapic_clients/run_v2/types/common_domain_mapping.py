# -*- coding: utf-8 -*-
# Copyright 2025 Google LLC
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
from __future__ import annotations

from typing import MutableMapping, MutableSequence

import proto  # type: ignore


__protobuf__ = proto.module(
    package='google.cloud.run.v2',
    manifest={
        'ResourceRecord',
    },
)


class ResourceRecord(proto.Message):
    r"""A DNS resource record.

    Attributes:
        name (str):
            Name of the resource record relative to its apex domain,
            e.g. ``www`` for ``www.example.com``. Omitted for apex
            records.
        data (str):
            Data for this record. Values vary by record
            type, as defined in RFC 1035 (section 5) and RFC
            1034 (section 3.6.1).
        type_ (googlecloudsdk.generated_clients.gapic_clients.run_v2.types.ResourceRecord.RecordType):
            Resource record type. Example: ``AAAA``.
    """
    class RecordType(proto.Enum):
        r"""A resource record type.

        Values:
            RECORD_TYPE_UNSPECIFIED (0):
                An unknown resource record.
            A (1):
                An A resource record. Data is an IPv4
                address.
            AAAA (2):
                An AAAA resource record. Data is an IPv6
                address.
            CNAME (3):
                A CNAME resource record. Data is a domain
                name to be aliased.
        """
        RECORD_TYPE_UNSPECIFIED = 0
        A = 1
        AAAA = 2
        CNAME = 3

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    data: str = proto.Field(
        proto.STRING,
        number=2,
    )
    type_: RecordType = proto.Field(
        proto.ENUM,
        number=3,
        enum=RecordType,
    )


__all__ = tuple(sorted(__protobuf__.manifest))
