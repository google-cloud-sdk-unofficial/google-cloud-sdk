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

"""Utilities for snapshot recycle bin policy."""

import json

from apitools.base.py import encoding as apitools_encoding


def _RulesValueEncoder(message, unused_encoder=None):
  """Encoder for SnapshotRecycleBinPolicy.RulesValue to support rule removal."""
  py_object = {}
  for item in message.additionalProperties:
    if item.value is None:
      py_object[item.key] = None
    else:
      py_object[item.key] = apitools_encoding.MessageToDict(item.value)
  return json.dumps(py_object)


def _RulesValueDecoder(unused_data, unused_decoder=None):
  """Decoder for SnapshotRecycleBinPolicy.RulesValue to support rule removal."""
  return None


def RegisterRulesValueCodec(messages):
  """Registers custom codec for SnapshotRecycleBinPolicy.RulesValue."""
  apitools_encoding.RegisterCustomMessageCodec(
      encoder=_RulesValueEncoder, decoder=_RulesValueDecoder
  )(messages.SnapshotRecycleBinPolicy.RulesValue)
