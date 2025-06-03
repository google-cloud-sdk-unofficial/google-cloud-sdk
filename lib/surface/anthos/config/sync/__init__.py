# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""The gcloud anthos config sync command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Deprecate(
    # In 2 weeks, set to True. In 4 weeks, delete the command group and
    # associated tests/utils.
    is_removed=False,
    warning=(
        'The `gcloud alpha anthos config sync` command group is deprecated and'
        ' will be removed in an upcoming release. Use the [nomos command line'
        ' tool](https://cloud.google.com/kubernetes-engine/enterprise/config-sync/docs/how-to/nomos-command)'
        ' or the Google Cloud console instead.'
    ),
    error=(
        'The `gcloud alpha anthos config sync` command group has been removed.'
        ' Use the [nomos command line'
        ' tool](https://cloud.google.com/kubernetes-engine/enterprise/config-sync/docs/how-to/nomos-command)'
        ' or the Google Cloud console instead.'
    ),
)
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AnthosConfigSync(base.Group):
  """Anthos config sync command group."""
