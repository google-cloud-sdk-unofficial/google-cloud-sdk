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
"""The command group for the Onboarding API."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Onboarding(base.Group):
  """Manage user onboarding sessions on Google Cloud."""

  category = base.MANAGEMENT_TOOLS_CATEGORY

  def Filter(self, context, args):
    del context
    base.DisableUserProjectQuota()
    if args.IsKnownAndSpecified('billing_project'):
      raise calliope_exceptions.InvalidArgumentException(
          '--billing-project',
          'The [--billing-project] flag is not supported for onboarding.',
      )
    if args.IsKnownAndSpecified('project'):
      raise calliope_exceptions.InvalidArgumentException(
          '--project',
          'The [--project] flag is not supported for onboarding.',
      )
