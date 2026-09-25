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


def GetProxyInfo(properties_module=None):
  """Returns the proxy string for use by requests from gcloud properties.

  Args:
    properties_module: Module, optional properties module to read proxy settings
      from.

  Returns:
    str or None: The proxy URL string if configured, otherwise None.

  See https://requests.readthedocs.io/en/master/user/advanced/#proxies.
  """
  if not properties_module:
    return None

  proxy_type = properties_module.VALUES.proxy.proxy_type.Get()
  proxy_address = properties_module.VALUES.proxy.address.Get()
  proxy_port = properties_module.VALUES.proxy.port.GetInt()

  proxy_prop_set = len(
      [f for f in (proxy_type, proxy_address, proxy_port) if f]
  )
  if proxy_prop_set > 0 and proxy_prop_set != 3:
    raise properties_module.InvalidValueError(
        'Please set all or none of the following properties: '
        'proxy/type, proxy/address and proxy/port'
    )

  if not proxy_prop_set:
    return

  proxy_rdns = properties_module.VALUES.proxy.rdns.GetBool()
  proxy_user = properties_module.VALUES.proxy.username.Get()
  proxy_pass = properties_module.VALUES.proxy.password.Get()

  http_proxy_type = PROXY_TYPE_MAP[proxy_type]
  if http_proxy_type == socks.PROXY_TYPE_SOCKS4:
    proxy_scheme = 'socks4a' if proxy_rdns else 'socks4'
  elif http_proxy_type == socks.PROXY_TYPE_SOCKS5:
    proxy_scheme = 'socks5h' if proxy_rdns else 'socks5'
  elif http_proxy_type == socks.PROXY_TYPE_HTTP:
    proxy_scheme = 'http'
  else:
    raise ValueError('Unsupported proxy type: {}'.format(proxy_type))

  if proxy_user or proxy_pass:
    proxy_auth = ':'.join(
        urllib.parse.quote(x) or '' for x in (proxy_user, proxy_pass)
    )
    proxy_auth += '@'
  else:
    proxy_auth = ''
  return '{}://{}{}:{}'.format(
      proxy_scheme, proxy_auth, proxy_address, proxy_port
  )
