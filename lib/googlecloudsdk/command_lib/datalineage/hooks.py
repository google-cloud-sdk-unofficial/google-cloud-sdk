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
"""Hooks for Data Lineage commands."""

from apitools.base.py import encoding
from apitools.base.py import extra_types
from googlecloudsdk.core import yaml


def SetProcessNameInBody(ref, args, req):
  """Set the process name in the request body."""
  del args
  if req.googleCloudDatacatalogLineageV1Process is not None:
    req.googleCloudDatacatalogLineageV1Process.name = ref.RelativeName()
  return req


def ParseAttributeValue(value):
  """Parse attribute value as YAML/JSON and convert to JsonValue message."""
  try:
    parsed_python_value = yaml.load(value)
  except Exception:  # pylint: disable=broad-except
    parsed_python_value = value
  return encoding.PyValueToMessage(extra_types.JsonValue, parsed_python_value)
