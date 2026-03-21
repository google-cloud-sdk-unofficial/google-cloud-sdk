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
"""Read only commands for Vm Extensions used in Global Vm Extension Policies."""

import textwrap

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class GlobalVmExtensionPolicies(base.Group):
  """Read only commands for Global Vm Extension Policies.

  These commands provide information on Vm Extensions available for use within
  VM Extension Policies at the global level.
  """


GlobalVmExtensionPolicies.category = base.INFO_CATEGORY

GlobalVmExtensionPolicies.detailed_help = {
    'DESCRIPTION': textwrap.dedent("""
        Commands for getting info on Vm Extensions used in Vm Extension Policies.
    """),
}
