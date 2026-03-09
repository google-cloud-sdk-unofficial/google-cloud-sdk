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
"""Flags for compute composite-health-checks commands."""

from googlecloudsdk.command_lib.compute import flags


def CompositeHealthCheckArgument(required=True, plural=False):
  return flags.ResourceArgument(
      name='COMPOSITE_HEALTH_CHECK',
      resource_name='composite health check',
      regional_collection='compute.regionCompositeHealthChecks',
      required=required,
      plural=plural,
  )
