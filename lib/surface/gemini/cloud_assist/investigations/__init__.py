# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""The command group for the investigations CLI."""


from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.gemini import cloud_assist


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class InvestigationsAlpha(base.Group):
  """Create and manage Gemini Cloud Assist investigations."""

  category = base.UNCATEGORIZED_CATEGORY

  @staticmethod
  def Args(parser):
    parser.display_info.AddTransforms({
        "input_observation_short": cloud_assist.InputObservationShort,
        "input_observation_detailed": cloud_assist.InputObservationDetailed,
        "observation_short": cloud_assist.ObservationShort,
        "observation_detailed": cloud_assist.ObservationDetailed,
        "hypothesis_observation_short": cloud_assist.HypothesisObservationShort,
        "hypothesis_observation_detailed": (
            cloud_assist.HypothesisObservationDetailed
        ),
        "investigation_short": cloud_assist.InvestigationShort,
        "investigation_detailed": cloud_assist.InvestigationDetailed,
    })
