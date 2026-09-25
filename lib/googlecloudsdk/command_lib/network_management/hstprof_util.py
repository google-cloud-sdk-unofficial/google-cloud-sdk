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
"""Utilities for `gcloud network-management hstprof` commands."""

from __future__ import annotations

import datetime
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core.util import times


def GetDurationString(value):
  """Formats duration integer into a protobuf duration string (e.g., '600s')."""
  if value is None:
    return None
  return f'{value}s'


def ValidateDestinationUri(value):
  """Validates that destinationUri starts with gs://."""
  if value and not value.startswith('gs://'):
    raise calliope_exceptions.InvalidArgumentException(
        '--destination-uri', 'must begin with "gs://".'
    )
  return value


def FormatDateTimeAsRfc3339(dt: datetime.datetime | None) -> str | None:
  """Formats a datetime object into an RFC 3339 string.

  Args:
    dt: The datetime object to format. Can be None.

  Returns:
    A string representation of the datetime in RFC 3339 format, or None if dt
    is None.
  """
  if dt is None:
    return None
  return times.FormatDateTime(dt, '%Y-%m-%dT%H:%M:%S.%6f%Ez')

