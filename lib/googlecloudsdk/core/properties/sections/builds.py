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
"""Contains the properties for the 'builds' section."""

from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.validators import _BuildTimeoutValidator


class _SectionBuilds(_Section):
  """Contains the properties for the 'builds' section."""

  def __init__(self):
    super(_SectionBuilds, self).__init__('builds')

    self.region = self._Add(
        'region',
        help_text=(
            'Default region to use when working with Cloud Build resources.'
            ' When a `--region` flag is required but not provided, the command'
            ' will fall back to this value, if set.'
        ),
    )
    self.timeout = self._Add(
        'timeout',
        validator=_BuildTimeoutValidator,
        help_text=(
            'Timeout, in seconds, to wait for builds to complete. If '
            'unset, defaults to 10 minutes.'
        ),
    )
    self.check_tag = self._AddBool(
        'check_tag',
        default=True,
        hidden=True,
        help_text=(
            'If True, validate that the --tag value to builds '
            'submit is in the gcr.io, *.gcr.io, or *.pkg.dev namespace.'
        ),
    )
    # TODO(b/118509363): Remove this after its default is True.
    self.use_kaniko = self._AddBool(
        'use_kaniko',
        default=False,
        help_text=(
            'If True, kaniko will be used to build images described by '
            'a Dockerfile, instead of `docker build`.'
        ),
    )
    self.kaniko_cache_ttl = self._Add(
        'kaniko_cache_ttl',
        default=6,
        help_text=(
            'TTL, in hours, of cached layers when using Kaniko. If zero, '
            'layer caching is disabled.'
        ),
    )
    self.kaniko_image = self._Add(
        'kaniko_image',
        default='gcr.io/kaniko-project/executor:latest',
        hidden=True,
        help_text=(
            'Kaniko builder image to use when use_kaniko=True. Defaults '
            'to gcr.io/kaniko-project/executor:latest'
        ),
    )
