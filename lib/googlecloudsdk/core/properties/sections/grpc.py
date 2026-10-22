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
"""Contains the properties for the 'grpc' section."""

import functools

from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.validators import _IntegerValidator


class _SectionGrpc(_Section):
  """Contains the properties for gRPC clients."""

  def __init__(self):
    super(_SectionGrpc, self).__init__('grpc', hidden=True)
    self.enable_http2_bdp_probe = self._AddBool(
        'enable_http2_bdp_probe',
        default=False,
        hidden=True,
        help_text='If True, gRPC will send BDP probes to estimate bandwidth.',
    )
    self.http2_lookahead_bytes = self._Add(
        'http2_lookahead_bytes',
        default=0,
        hidden=True,
        validator=_IntegerValidator,
        help_text='The number of bytes gRPC will look ahead in the TCP stream.',
    )
    self.max_metadata_size = self._Add(
        'max_metadata_size',
        hidden=True,
        validator=functools.partial(_IntegerValidator, 'max_metadata_size'),
        help_text='Maximum metadata size (soft limit), in bytes.',
    )
