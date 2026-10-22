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
"""Contains the properties for the 'proxy' section."""

from googlecloudsdk.core.properties.exceptions import InvalidValueError
from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.util import http_proxy_types


class _SectionProxy(_Section):
  """Contains the properties for the 'proxy' section."""

  def __init__(self):
    super(_SectionProxy, self).__init__('proxy')
    self.address = self._Add(
        'address', help_text='Hostname or IP address of proxy server.'
    )
    self.port = self._Add(
        'port', help_text='Port to use when connected to the proxy server.'
    )
    self.rdns = self._Add(
        'rdns',
        default=True,
        help_text=(
            'If True, DNS queries will not be performed locally, and instead,'
            ' handed to the proxy to resolve. This is default behavior.'
        ),
    )
    self.username = self._Add(
        'username',
        help_text=(
            'Username to use when connecting, if the proxy '
            'requires authentication.'
        ),
    )
    self.password = self._Add(
        'password',
        help_text=(
            'Password to use when connecting, if the proxy '
            'requires authentication.'
        ),
    )

    valid_proxy_types = sorted(http_proxy_types.PROXY_TYPE_MAP.keys())

    def ProxyTypeValidator(proxy_type):
      if proxy_type is not None and proxy_type not in valid_proxy_types:
        raise InvalidValueError(
            'The proxy type property value [{0}] is not valid. '
            'Possible values: [{1}].'.format(
                proxy_type, ', '.join(valid_proxy_types)
            )
        )

    self.proxy_type = self._Add(
        'type',
        help_text=(
            'Type of proxy being used.  Supported proxy types are:'
            ' [{0}].'.format(', '.join(valid_proxy_types))
        ),
        validator=ProxyTypeValidator,
        choices=valid_proxy_types,
    )
