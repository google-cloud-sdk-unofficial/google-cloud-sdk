# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""The command to get the status of the Cloud Build Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.fleet.features import base


@gbase.Hidden
class Describe(base.DescribeCommand):
  """Obtain the status of the Cloud Build hybrid pools feature.

  Displays the status of the Cloud Build hybrid pools feature in the fleet.

  ## EXAMPLES

  To get the status of the Cloud Build hybrid pools feature, run:

    $ {command}
  """

  feature_name = 'cloudbuild'

  def Run(self, args):
    feature = self.GetFeature(v1alpha1=True)

    feature_status = []
    if feature is None or feature.featureState is None:
      return feature_status
    feature_status.append({'NAME': feature.name})
    feature_status.append(
        {'LIFECYCLESTATE': feature.featureState.lifecycleState})
    feature_status.append({'CREATE TIME': feature.createTime})
    feature_status.append({'UPDATE TIME': feature.updateTime})
    return feature_status
