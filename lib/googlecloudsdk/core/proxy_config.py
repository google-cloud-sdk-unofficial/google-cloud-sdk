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

"""Utilities for resolving configured proxy URLs from gcloud properties."""

import typing

from googlecloudsdk.core import properties
from googlecloudsdk.core.util import http_proxy_types


def GetProxyInfo() -> typing.Optional[str]:
  """Returns the proxy string for use by requests from gcloud properties.

  Returns:
    str or None: The proxy URL string if configured, otherwise None.

  Raises:
    properties.InvalidValueError: If a partial proxy configuration is set, or
      a proxy property has an invalid value (for example, an unknown proxy
      type, which the property validator rejects before it can be looked up).

  See https://requests.readthedocs.io/en/master/user/advanced/#proxies.
  """
  proxy_type = properties.VALUES.proxy.proxy_type.Get()
  proxy_address = properties.VALUES.proxy.address.Get()
  proxy_port = properties.VALUES.proxy.port.GetInt()

  # Validate the core proxy properties before reading the optional ones, so
  # that a malformed optional property cannot mask this error.
  try:
    proxy_configured = http_proxy_types.IsProxyConfigured(
        proxy_type, proxy_address, proxy_port
    )
  except ValueError as e:
    raise properties.InvalidValueError(str(e)) from e

  if not proxy_configured:
    return None

  return http_proxy_types.FormatProxyUrl(
      proxy_type=proxy_type,
      proxy_address=proxy_address,
      proxy_port=proxy_port,
      proxy_rdns=properties.VALUES.proxy.rdns.GetBool(),
      proxy_user=properties.VALUES.proxy.username.Get(),
      proxy_pass=properties.VALUES.proxy.password.Get(),
  )
