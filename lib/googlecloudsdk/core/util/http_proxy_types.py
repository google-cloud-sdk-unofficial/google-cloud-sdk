# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Maps from proxy type names to httplib2.socks enum values, and vice versa."""

from six.moves import urllib
import socks

PROXY_TYPE_MAP = {
    'socks4': socks.PROXY_TYPE_SOCKS4,
    'socks5': socks.PROXY_TYPE_SOCKS5,
    'http': socks.PROXY_TYPE_HTTP,
    # For https requests, http_no_tunnel is equivalent to http
    'http_no_tunnel': socks.PROXY_TYPE_HTTP,
}

REVERSE_PROXY_TYPE_MAP = {
    socks.PROXY_TYPE_SOCKS4: 'socks4',
    socks.PROXY_TYPE_SOCKS5: 'socks5',
    socks.PROXY_TYPE_HTTP: 'http',
}


def IsProxyConfigured(proxy_type, proxy_address, proxy_port):
  """Checks whether the core proxy settings describe a usable proxy.

  Args:
    proxy_type: str, type of proxy ('http', 'socks4', 'socks5', etc.).
    proxy_address: str, proxy host address.
    proxy_port: int, proxy port number.

  Returns:
    bool: True if all three core values are set, False if none of them are set.

  Raises:
    ValueError: If only some of the core values are set.
  """
  proxy_prop_set = len(
      [f for f in (proxy_type, proxy_address, proxy_port) if f]
  )
  if proxy_prop_set > 0 and proxy_prop_set != 3:
    raise ValueError(
        'Please set all or none of the following properties: '
        'proxy/type, proxy/address and proxy/port'
    )
  return proxy_prop_set == 3


def FormatProxyUrl(
    proxy_type,
    proxy_address,
    proxy_port,
    proxy_rdns=False,
    proxy_user=None,
    proxy_pass=None,
):
  """Formats a proxy URL string from explicit primitive configuration values.

  Args:
    proxy_type: str, type of proxy ('http', 'socks4', 'socks5', etc.).
    proxy_address: str, proxy host address.
    proxy_port: int, proxy port number.
    proxy_rdns: bool, whether to use remote DNS resolution.
    proxy_user: str, optional proxy username.
    proxy_pass: str, optional proxy password.

  Returns:
    str or None: The proxy URL string if configured, otherwise None.

  Raises:
    KeyError: If proxy_type is not in PROXY_TYPE_MAP.
    ValueError: If partial proxy configuration is specified.
  """
  if not IsProxyConfigured(proxy_type, proxy_address, proxy_port):
    return None

  http_proxy_type = PROXY_TYPE_MAP[proxy_type]
  if http_proxy_type == socks.PROXY_TYPE_SOCKS4:
    proxy_scheme = 'socks4a' if proxy_rdns else 'socks4'
  elif http_proxy_type == socks.PROXY_TYPE_SOCKS5:
    proxy_scheme = 'socks5h' if proxy_rdns else 'socks5'
  elif http_proxy_type == socks.PROXY_TYPE_HTTP:
    proxy_scheme = 'http'

  if proxy_user or proxy_pass:
    proxy_auth = (
        ':'.join(urllib.parse.quote(x or '') for x in (proxy_user, proxy_pass))
        + '@'
    )
  else:
    proxy_auth = ''
  return '{}://{}{}:{}'.format(
      proxy_scheme, proxy_auth, proxy_address, proxy_port
  )
