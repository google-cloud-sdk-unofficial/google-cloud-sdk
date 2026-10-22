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
"""Hooks for mldiagnostics commands."""

from googlecloudsdk.calliope import exceptions


def RemoveAnalyzerReports(response, args):
  """Removes analyzerReports from the response to match list command behavior."""
  del args
  for event in response:
    if hasattr(event, 'analyzerReports'):
      event.analyzerReports = []
    yield event


def ValidateProfilerSessionCaptureRequest(unused_ref, args, request):
  """Validates arguments for profiler-session capture command."""
  if args.kind == 'on-demand' and not args.IsSpecified('duration'):
    raise exceptions.RequiredArgumentException(
        '--duration',
        'Duration is required when --kind is on-demand.',
    )
  return request
