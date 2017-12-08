# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Commands for creating and deleting maintenance policies."""
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class MaintenancePolicies(base.Group):
  """Create and delete maintenance policies."""


MaintenancePolicies.detailed_help = {
    'brief': 'Create Google Compute Engine Maintenance Policies.',
    'DESCRIPTION': """\
      Currently Maintenance Policies are only available for instances.
      Maintenance policies for instances let you define time windows
      in which live migrations can take place.
    """
}
