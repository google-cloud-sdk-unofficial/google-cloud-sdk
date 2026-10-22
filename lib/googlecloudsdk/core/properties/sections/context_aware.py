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
"""Contains the properties for the 'context_aware' section."""

from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.validators import ExistingAbsoluteFilepathValidator


class _SectionContextAware(_Section):
  """Contains the properties for the 'context_aware' section."""

  def __init__(self):
    super(_SectionContextAware, self).__init__('context_aware')
    self.use_client_certificate = self._AddBool(
        'use_client_certificate',
        help_text=(
            'If True, use client certificate to authorize user '
            'device using Context-aware access. This includes user login '
            'as well. Some services may not support client certificate '
            'authorization. If a command sends requests to such services, the '
            'client certificate will not be validated. '
            'Run `gcloud topic client-certificate` for list of services '
            'supporting this feature.'
        ),
        default=False,
    )
    # Only for tests. It is valuable to test that the mTLS endpoints are serving
    # without involving the policy enforcement. The mTLS endpoints are expected
    # to behave identically to the regular endpoints without policy enforcement.
    self.always_use_mtls_endpoint = self._AddBool(
        'always_use_mtls_endpoint',
        help_text=(
            'If True, use the mTLS endpoints regardless of the value of '
            'context_aware/use_client_certificate.'
        ),
        default=False,
        hidden=True,
    )
    self.auto_discovery_file_path = self._Add(
        'auto_discovery_file_path',
        validator=ExistingAbsoluteFilepathValidator,
        help_text='File path for auto discovery configuration file.',
        hidden=True,
    )
    self.certificate_config_file_path = self._Add(
        'certificate_config_file_path',
        validator=ExistingAbsoluteFilepathValidator,
        help_text='File path for certificate configuration file.',
        hidden=True,
    )
    self.use_ecp_http_proxy = self._AddBool(
        'use_ecp_http_proxy',
        help_text=(
            'If True, use the ECP HTTP proxy for requests. This property is'
            ' used to determine if the ECP HTTP proxy should be used. If set to'
            ' True, the ECP HTTP proxy will be used for all ECP requests. If'
            ' set to False, the ECP HTTP proxy will not be used.'
        ),
        default=True,
        hidden=True,
    )
    self.use_mtls_for_grpc = self._AddBool(
        'use_mtls_for_grpc',
        help_text=(
            'If True, use mTLS for gRPC connections when Enterprise Certificate'
            ' is configured.'
        ),
        default=False,
        hidden=True,
    )
