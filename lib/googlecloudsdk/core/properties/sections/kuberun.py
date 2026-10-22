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
"""Contains the properties for the 'kuberun' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionKubeRun(_Section):
  """Contains the properties for the 'kuberun' section."""

  def __init__(self):
    super(_SectionKubeRun, self).__init__('kuberun')
    self.enable_experimental_commands = self._AddBool(
        'enable_experimental_commands',
        help_text=(
            'If True, experimental KubeRun commands will not prompt to '
            'continue.'
        ),
        hidden=True,
    )

    self.environment = self._Add(
        'environment',
        help_text=(
            'If set, this environment will be used as the deployment'
            'target in all KubeRun commands.'
        ),
        hidden=True,
    )

    self.cluster = self._Add(
        'cluster',
        help_text=(
            'ID of the cluster or fully qualified identifier for the cluster'
        ),
        hidden=True,
    )

    self.cluster_location = self._Add(
        'cluster_location',
        help_text='Zone or region in which the cluster is located.',
        hidden=True,
    )

    self.use_kubeconfig = self._AddBool(
        'use_kubeconfig',
        help_text='Use the default or provided kubectl config file.',
        hidden=True,
    )

    self.kubeconfig = self._Add(
        'kubeconfig',
        help_text='Absolute path to your kubectl config file.',
        hidden=True,
    )

    self.context = self._Add(
        'context',
        help_text='Name of the context in your kubectl config file to use.',
        hidden=True,
    )
