# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Module for common transport utilities, such as request wrapping.

All core transport primitives have been decoupled into transport_base.py
to break circular dependencies between requests.py and transport.py.
This module re-exports all symbols for backward compatibility.
"""

from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import transport_base

# Re-exported for backward compatibility with transport.exceptions.DryRunError.
# Note: core/transport does not import calliope/exceptions to enforce strict
# infrastructure layering hierarchy (core -> calliope).
exceptions = core_exceptions
DryRunError = transport_base.DryRunError

AddQueryParam = transport_base.AddQueryParam
AppendToHeader = transport_base.AppendToHeader
ENCODING = transport_base.ENCODING
GetAndCacheArchitecture = transport_base.GetAndCacheArchitecture
GetDefaultTimeout = transport_base.GetDefaultTimeout
GetValidMCPMetricsString = transport_base.GetValidMCPMetricsString
Handler = transport_base.Handler
INVOCATION_ID = transport_base.INVOCATION_ID
IsTokenUri = transport_base.IsTokenUri
LogRequest = transport_base.LogRequest
LogRequestDryRun = transport_base.LogRequestDryRun
LogResponse = transport_base.LogResponse
MakeUserAgentString = transport_base.MakeUserAgentString
MaybePrependToHeader = transport_base.MaybePrependToHeader
RecordStartTime = transport_base.RecordStartTime
ReportDuration = transport_base.ReportDuration
Request = transport_base.Request
RequestWrapper = transport_base.RequestWrapper
Response = transport_base.Response
SetHeader = transport_base.SetHeader
TOKEN_URIS = transport_base.TOKEN_URIS
ValidateMCPMetricsFormat = transport_base.ValidateMCPMetricsFormat
