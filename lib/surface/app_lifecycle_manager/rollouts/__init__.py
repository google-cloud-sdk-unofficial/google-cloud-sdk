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
"""The rollouts command group for the App Lifecycle Manager CLI."""

from googlecloudsdk.calliope import base


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Saas(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {
      'brief': 'Manage App Lifecycle Manager rollouts.',
      'DESCRIPTION': """
          Manage App Lifecycle Manager rollouts. A rollout represents a single
          execution of rolling out a release to the target units, including
          its results. The rollout follows the settings of the rollout kind
          that it stems from.
      """,
      'EXAMPLES': """
          To create a rollout named `my-rollout` in location `us-central1` that
          rolls out the release `my-release` according to the rollout kind
          `my-rollout-kind`, run:

            $ {command} create my-rollout --location=us-central1 --release=my-release --rollout-kind=my-rollout-kind

          To list the names of all rollouts in location `us-central1`, run:

            $ {command} list --location=us-central1 --format="value(name)"

          To pause the rollout named `my-rollout` in location `us-central1`,
          run:

            $ {command} update my-rollout --location=us-central1 --control-action=pause
      """,
  }


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SaasAlpha(base.Group):
  category = base.SAAS_CATEGORY
  detailed_help = {'brief': 'Manage App Lifecycle Manager rollouts.'}
