# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to enable the telemetry."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import telemetry as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags

_EXAMPLES = """
To enable monitoring for the telemetry, run:

$ {command} --enable-monitoring

To disable monitoring for the telemetry, run:

$ {command} --disable-monitoring
"""


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update the telemetry."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    flags.AddTelemetryUpdateFlags(parser)

  def Run(self, args):
    """Runs the update command."""
    client = apis.TelemetryClient()
    return client.Update(args)


