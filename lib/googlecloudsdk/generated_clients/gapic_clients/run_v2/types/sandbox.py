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

from googlecloudsdk.generated_clients.gapic_clients.run_v2.types import k8s_min


__protobuf__ = proto.module(
    package='google.cloud.run.v2',
    manifest={
        'SandboxConfiguration',
    },
)


class SandboxConfiguration(proto.Message):
    r"""Configuration for sandboxes.

    Attributes:
        templates (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.run_v2.types.Container]):
            Required. Container templates that can be launched through
            the ``sandbox`` CLI.
    """

    templates: MutableSequence[k8s_min.Container] = proto.RepeatedField(
        proto.MESSAGE,
        number=2,
        message=k8s_min.Container,
    )


__all__ = tuple(sorted(__protobuf__.manifest))
