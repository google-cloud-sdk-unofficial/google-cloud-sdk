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
"""Command group for Machine Learning."""

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Ml(base.Group):
  """Use Google Cloud machine learning capabilities."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class MlAlpha(base.Group):
  """Use Google Cloud machine learning capabilities."""

  def Filter(self, unused_context, unused_args):
    if not properties.VALUES.billing.quota_project.IsExplicitlySet():
      # Explicitly enable the new quota header for alpha commands only if the
      # user doesn't have a preference specifically set.
      properties.VALUES.billing.quota_project.Set(
          properties.VALUES.billing.CURRENT_PROJECT)
