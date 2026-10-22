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
"""Contains the properties for the 'container' section."""

from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.validators import _BuildTimeoutValidator


class _SectionContainer(_Section):
  """Contains the properties for the 'container' section."""

  def __init__(self):
    super(_SectionContainer, self).__init__('container')
    self.cluster = self._Add(
        'cluster',
        help_text=(
            'Name of the cluster to use by default when '
            'working with Kubernetes Engine.'
        ),
    )
    self.use_client_certificate = self._AddBool(
        'use_client_certificate',
        default=False,
        help_text=(
            "If True, use the cluster's client certificate to "
            'authenticate to the cluster API server.'
        ),
    )
    self.use_app_default_credentials = self._AddBool(
        'use_application_default_credentials',
        default=False,
        help_text=(
            'If True, use application default credentials to authenticate'
            ' to the cluster API server.'
        ),
    )

    self.build_timeout = self._Add(
        'build_timeout',
        validator=_BuildTimeoutValidator,
        help_text=(
            'Timeout, in seconds, to wait for container builds to complete.'
        ),
    )
    self.build_check_tag = self._AddBool(
        'build_check_tag',
        default=True,
        hidden=True,
        help_text=(
            'If True, validate that the --tag value to container builds '
            'submit is in the gcr.io or *.gcr.io namespace.'
        ),
    )
