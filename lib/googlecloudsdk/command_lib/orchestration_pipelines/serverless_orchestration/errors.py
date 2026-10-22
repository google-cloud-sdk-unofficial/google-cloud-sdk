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
"""Error types shared by the Serverless Orchestration deploy/trigger flows."""

from googlecloudsdk.core import exceptions as core_exceptions


class ServerlessOrchestrationError(core_exceptions.Error):
  """Base error for Serverless Orchestration pipeline operations."""


class NotImplementedYetError(ServerlessOrchestrationError):
  """Raised by placeholder implementations that later CLs in this stack replace.

  A `core_exceptions.Error` so that Calliope prints a formatted error instead
  of a stack trace if a placeholder is reached.
  """


class PipelineLoadError(ServerlessOrchestrationError):
  """Raised when a pipeline or deployment YAML is unreadable or invalid."""


class PackagingError(ServerlessOrchestrationError):
  """Raised when the artifacts of a pipeline action cannot be packaged."""


class UploadError(ServerlessOrchestrationError):
  """Raised when an artifact upload fails or an existing object differs."""
