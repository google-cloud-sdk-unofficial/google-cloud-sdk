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
"""The rollout-kinds command group for the App Lifecycle Manager CLI."""

from googlecloudsdk.calliope import base


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Saas(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {
      'brief': 'Manage App Lifecycle Manager rollout kinds.',
      'DESCRIPTION': """
          Manage App Lifecycle Manager rollout kinds. A rollout kind describes
          the settings of rollout execution for the units of a unit kind,
          such as the orchestration strategy and error budget.
      """,
      'EXAMPLES': """
          To create a rollout kind named `my-rollout-kind` for the unit kind
          `my-unit-kind` in location `us-central1`, run:

            $ {command} create my-rollout-kind --location=us-central1 --unit-kind=my-unit-kind

          To list the names of all rollout kinds in location `us-central1`, run:

            $ {command} list --location=us-central1 --format="value(name)"

          To describe the rollout kind named `my-rollout-kind` in location
          `us-central1`, run:

            $ {command} describe my-rollout-kind --location=us-central1
      """,
  }


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SaasAlpha(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {'brief': 'Manage App Lifecycle Manager rollout-kinds.'}
