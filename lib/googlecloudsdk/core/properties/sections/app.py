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
"""Contains the properties for the 'app' section."""

from googlecloudsdk.core.properties.providers import PROVIDERS
from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.validators import _BuildTimeoutValidator


class _SectionApp(_Section):
  """Contains the properties for the 'app' section."""

  def __init__(self):
    super(_SectionApp, self).__init__('app')
    self.promote_by_default = self._AddBool(
        'promote_by_default',
        help_text=(
            'If True, when deploying a new version of a service, that version'
            ' will be promoted to receive all traffic for the service. This'
            ' property can be overridden with the `--promote-by-default` or'
            ' `--no-promote-by-default` flags.'
        ),
        default=True,
    )
    self.stop_previous_version = self._AddBool(
        'stop_previous_version',
        help_text=(
            'If True, when deploying a new version of a service, the previously'
            ' deployed version is stopped. If False, older versions must be'
            ' stopped manually.'
        ),
        default=True,
    )
    self.trigger_build_server_side = self._AddBool(
        'trigger_build_server_side', hidden=True, default=None
    )
    self.use_flex_with_buildpacks = self._AddBool(
        'use_flex_with_buildpacks', hidden=True, default=None
    )
    self.cloud_build_timeout = self._Add(
        'cloud_build_timeout',
        validator=_BuildTimeoutValidator,
        help_text=(
            'Timeout, in seconds, to wait for Docker builds to '
            'complete during deployments. All Docker builds now use the '
            'Cloud Build API.'
        ),
    )
    self.container_builder_image = self._Add(
        'container_builder_image',
        default='gcr.io/cloud-builders/docker',
        hidden=True,
    )
    self.use_appengine_api = self._AddBool(
        'use_appengine_api', default=True, hidden=True
    )
    # This property is currently ignored except on OS X Sierra or beta
    # deployments.
    # There's a theoretical benefit to exceeding the number of cores available,
    # since the task is bound by network/API latency among other factors, and
    # mini-benchmarks validated this (I got speedup from 4 threads to 8 on a
    # 4-core machine).
    self.num_file_upload_threads = self._Add(
        'num_file_upload_threads', default=None, hidden=True
    )

    self.runtime_root = self._Add(
        'runtime_root', callbacks=[PROVIDERS['GetRuntimeRoot']], hidden=True
    )

    # Whether or not to use the (currently under-development) Flex Runtime
    # Builders, as opposed to Externalized Runtimes.
    #   True  => ALWAYS
    #   False => NEVER
    #   Unset => default behavior, which varies between beta/GA commands
    self.use_runtime_builders = self._Add(
        'use_runtime_builders',
        default=None,
        help_text=(
            'If set, opt in/out to a new code path for building '
            'applications using pre-fabricated runtimes that can be '
            'updated independently of client tooling. If not set, '
            'the default path for each runtime is used.'
        ),
    )
    # The Cloud Storage path prefix for the Flex Runtime Builder configuration
    # files. The configuration files will live at
    # "<PREFIX>/<runtime>-<version>.yaml", with an additional
    # "<PREFIX>/runtime.version" indicating the latest version.
    self.runtime_builders_root = self._Add(
        'runtime_builders_root', default='gs://runtime-builders/', hidden=True
    )
