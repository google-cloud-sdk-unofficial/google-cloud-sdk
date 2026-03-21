# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""This file defines utility functions for the orchestration pipelines models."""

import pytz
import re

_MONTHS = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT",
    "NOV", "DEC"
]
_DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]

_CRON_FIELDS = [
    ("minute", 0, 59, None),
    ("hour", 0, 23, None),
    ("day of month", 1, 31, None),
    ("month", 1, 12, _MONTHS),
    ("day of week", 0, 7, _DAYS),  # 0 or 7 can be Sunday
]

_FIELD_PATTERN = re.compile(r"^[0-9*\/\-,a-z]+$", re.IGNORECASE)


def _normalize_value(val, mapping):
    """Converts JAN->1, MON->1, etc., for range checking."""
    if val.isdigit():
        return int(val)
    if mapping:
        try:
            # Handle case-insensitive symbolic names
            return mapping.index(val.upper()) + (0 if mapping == _DAYS else 1)
        except ValueError:
            pass
    return None


def _check_part(part, min_v, max_v, mapping):
    """Validates a single part of a comma-separated list."""
    # Handle steps: */5 or 1-10/2
    if "/" in part:
        base, step = part.split("/", 1)
        if not (step.isdigit() and int(step) > 0):
            return False
        return _check_part(base, min_v, max_v, mapping)

    # Handle ranges: 1-5 or JAN-MAR
    if "-" in part:
        start_str, end_str = part.split("-", 1)
        start = _normalize_value(start_str, mapping)
        end = _normalize_value(end_str, mapping)

        if start is None or end is None:
            return False
        return min_v <= start <= max_v and min_v <= end <= max_v

    # Handle wildcards and constants
    if part == "*":
        return True

    val = _normalize_value(part, mapping)
    return val is not None and min_v <= val <= max_v


def is_valid_field(field_str, min_val, max_val, mapping):
    if not _FIELD_PATTERN.match(field_str):
        return False
    return all(
        _check_part(p, min_val, max_val, mapping)
        for p in field_str.split(","))


def check_cron_expression(value):
    if not value or not isinstance(value, str):
        raise ValueError("CRON expression must be a non-empty string.")

    aliases = [
        "@yearly", "@annually", "@monthly", "@weekly", "@daily", "@midnight",
        "@hourly"
    ]
    if value.strip().lower() in aliases:
        return

    parts = value.strip().split()
    if len(parts) != 5:
        raise ValueError(
            f"Invalid CRON expression (must have 5 fields): '{value}'")

    for (name, min_val, max_val, mapping), part in zip(_CRON_FIELDS, parts):
        if not is_valid_field(part, min_val, max_val, mapping):
            raise ValueError(f"Invalid {name} field: '{part}'")


def check_timezone(value):
    try:
        pytz.timezone(value)
    except (pytz.UnknownTimeZoneError, AttributeError, TypeError):
        raise ValueError(f"'{value}' is not a valid timezone")


def check_duration(value):
    """
    Validates that a string is a valid time duration (e.g., '30s', '5m', '2h').
    Allowed units: s (seconds), m (minutes), h (hours), d (days), w (weeks).
    """
    pattern = r"^(\s*\d+[smhdw]\s*)+$"

    if not isinstance(value, str):
        raise TypeError(
            f"Duration must be a string (e.g., '10m'), got {type(value).__name__}."
        )

    if not re.match(pattern, value.strip().lower()):
        raise ValueError(
            f"Invalid duration format: '{value}'. "
            "Expected format: <number><unit> (e.g., '1h 30m', '30s'). "
            "Valid units are: s, m, h, d, w.")


# ---------------------------------------------------------------------------
# Validators for attrs models (v1)
# ---------------------------------------------------------------------------
def validate_cron_expression(instance, attribute, value):
    try:
        check_cron_expression(value)
    except ValueError as e:
        raise ValueError(f"'{attribute.name}' error: {e}")


def validate_timezone(instance, attribute, value):
    try:
        check_timezone(value)
    except ValueError as e:
        raise ValueError(f"'{attribute.name}' error: {e}")


def validate_duration(instance, attribute, value):
    try:
        check_duration(value)
    except (ValueError, TypeError) as e:
        raise type(e)(f"'{attribute.name}' error: {e}")
