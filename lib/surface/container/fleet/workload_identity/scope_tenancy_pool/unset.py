# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""The command to unset the scope tenancy pool for a fleet."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from googlecloudsdk.calliope import base

from googlecloudsdk.command_lib.container.fleet.features import base as feature_base


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class Unset(feature_base.UpdateCommand):
  """Unset Scope Tenancy Pool.

  Unset the scope tenancy pool for a fleet.

  ## Examples

  To unset the scope tenancy pool, run:

    $ {command}
  """

  feature_name = 'workloadidentity'

  def Run(self, _):
    feature = self.messages.Feature(
        spec=self.messages.CommonFeatureSpec(
            workloadidentity=self.messages.WorkloadIdentityFeatureSpec(
                scopeTenancyPool=None
            )
        )
    )

    self.Update(['spec.workloadidentity.scopeTenancyPool'], feature)
