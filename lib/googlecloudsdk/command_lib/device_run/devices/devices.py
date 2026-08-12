# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions for Device Run devices."""

from typing import Any, Optional

_CAPACITY_PREFIX = 'CAPACITY_'
_AVAILABILITY_PREFIX = 'AVAILABILITY_'


def StripCapacityPrefix(capacity: Optional[Any]) -> Optional[str]:
  if capacity is None:
    return None
  return str(capacity).removeprefix(_CAPACITY_PREFIX)


def StripAvailabilityPrefix(availability: Optional[Any]) -> Optional[str]:
  if availability is None:
    return None
  return str(availability).removeprefix(_AVAILABILITY_PREFIX)
