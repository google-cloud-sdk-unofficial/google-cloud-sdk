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
"""Command group for Data Boundary control compliance summaries."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(ReleaseTrack.ALPHA)
class ControlSummaries(base.Group):
  """Read control compliance summaries of a framework compliance report."""

  detailed_help = {
      'DESCRIPTION': (
          """
        Read the control compliance summaries of a Data Boundary framework
        compliance report.
    """
      ),
  }
