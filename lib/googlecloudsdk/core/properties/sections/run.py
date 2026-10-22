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
"""Contains the properties for the 'run' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionRun(_Section):
  """Contains the properties for the 'run' section."""

  def __init__(self):
    super(_SectionRun, self).__init__('run')
    self.region = self._Add(
        'region',
        help_text=(
            'Default region to use when working with Cloud Run resources. When'
            ' a `--region` flag is required but not provided, the command will'
            ' fall back to this value, if set.'
        ),
    )

    self.namespace = self._Add(
        'namespace',
        help_text=(
            'Specific to working with Cloud on GKE or '
            'a Kubernetes cluster: Kubernetes namespace for the resource.'
        ),
        hidden=True,
    )

    self.cluster = self._Add(
        'cluster',
        help_text=(
            'ID of the cluster or fully qualified identifier for the cluster'
        ),
    )

    self.cluster_location = self._Add(
        'cluster_location',
        help_text='Zone or region in which the cluster is located.',
    )

    self.platform = self._Add(
        'platform',
        choices=['gke', 'managed', 'kubernetes'],
        default='managed',
        help_text='Target platform for running commands.',
    )

    self.enable_unified_build = self._Add(
        'enable_unified_build',
        default=False,
        hidden=True,
        help_text='Enables using Cloud Run API to orchestrate builds.',
    )
