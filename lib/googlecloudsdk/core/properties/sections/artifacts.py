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
"""Contains the properties for the 'artifacts' section."""

from googlecloudsdk.core.properties.types import _Section


class _SectionArtifacts(_Section):
  """Contains the properties for the 'artifacts' section."""

  def __init__(self):
    super(_SectionArtifacts, self).__init__('artifacts')

    self.repository = self._Add(
        'repository',
        help_text=(
            'Default repository to use when working with Artifact '
            'Registry resources. When a `repository` value is required but not '
            'provided, the command will fall back to this value, if set.'
        ),
    )

    self.location = self._Add(
        'location',
        help_text=(
            'Default location to use when working with Artifact Registry'
            ' resources. When a `location` value is required but not provided,'
            ' the command will fall back to this value, if set. If this value'
            ' is unset, the default location is `global` when `location` value'
            ' is optional.'
        ),
    )

    self.registry_endpoint_prefix = self._Add(
        'registry_endpoint_prefix',
        default='',
        hidden=True,
        help_text=(
            'Default prefix to use while interacting with Artifact '
            'Registry resources.'
        ),
    )

    self.domain = self._Add(
        'domain',
        default='pkg.dev',
        hidden=True,
        help_text=(
            'Default domain endpoint to use while interacting with '
            'Artifact Registry Docker resources.'
        ),
    )

    self.gcr_host = self._Add(
        'gcr_host',
        default='gcr.io',
        hidden=True,
        help_text=(
            'Default host to use while interacting with Container Registry '
            'Docker resources.'
        ),
    )

    self.max_notes_per_batch_request = self._Add(
        'max_notes_per_batch_request',
        default=1000,
        hidden=True,
        help_text='Default batching size for BatchCreateNotes requests.',
    )

    self.allow_unrecognized_registry = self._AddBool(
        'allow_unrecognized_registry',
        default=False,
        hidden=True,
        help_text=(
            'If set to true, bypass the check against the list of known'
            ' registries'
        ),
    )
