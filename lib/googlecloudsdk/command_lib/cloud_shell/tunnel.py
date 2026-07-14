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
"""WebSocket tunneling for Cloud Shell SSH."""

import socket
import ssl
import threading
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from requests import certs
import websocket
import websocket._exceptions as websocket_exceptions


class CloudShellTunnel:
  """Tunnels TCP traffic over a Cloud Shell WebSocket connection."""

  def __init__(self, host, jwt, local_port=0):
    self.host = host
    self.jwt = jwt
    self.local_port = local_port
    self.socket = None
    self.tcp_tunnel_open = False

  def Start(self):
    """Starts the local TCP server and listens for connections."""
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.socket.bind(('localhost', self.local_port))
    self.socket.listen(1)

    self.local_port = self.socket.getsockname()[1]
    log.status.Print(f'Listening on local port [{self.local_port}].')

    self.tcp_tunnel_open = True

    def Accept():
      while self.tcp_tunnel_open:
        try:
          conn, addr = self.socket.accept()
          self._AcceptConnection(conn, addr)
        except socket.error:
          if not self.tcp_tunnel_open:
            break
          raise

    self.thread = threading.Thread(target=Accept, daemon=True)
    self.thread.start()

  def Stop(self):
    """Stops the tunnel."""
    self.tcp_tunnel_open = False
    if self.socket:
      self.socket.close()
    log.status.Print('Tunnel stopped.')

  def _AcceptConnection(self, client, _):
    """Opens a WebSocket connection."""
    cert_reqs = ssl.CERT_REQUIRED
    ca_certs = certs.where()

    custom_ca_certs = properties.VALUES.core.custom_ca_certs_file.Get()
    no_validate = (
        properties.VALUES.auth.disable_ssl_validation.GetBool() or False
    )

    if no_validate:
      ca_certs = None
      cert_reqs = ssl.CERT_NONE
    if custom_ca_certs:
      ca_certs = custom_ca_certs

    # URL for Cloud Shell SSH WebSocket
    url = f'wss://{self.host}/_cloudshell/tcp/22'

    server = websocket.WebSocketApp(
        url,
        header={'Authorization': 'Bearer ' + self.jwt},
        on_open=lambda ws: self._ForwardClientToServer(client, ws),
        on_data=lambda ws, data, op, finished: client.sendall(data),
        on_error=lambda ws, e: self._OnWebsocketError(client, e),
        on_close=lambda ws, status, msg: client.close(),
    )

    def Run():
      proxy_type = properties.VALUES.proxy.proxy_type.Get()
      if proxy_type == 'http' or proxy_type == 'http_no_tunnel':
        http_proxy_host = properties.VALUES.proxy.address.Get()
        http_proxy_port = properties.VALUES.proxy.port.Get()
        http_proxy_auth = (
            properties.VALUES.proxy.username.Get(),
            properties.VALUES.proxy.password.Get(),
        )

        server.run_forever(
            sslopt={
                'cert_reqs': cert_reqs,
                'ca_certs': ca_certs,
            },
            proxy_type='http',
            http_proxy_host=http_proxy_host,
            http_proxy_port=http_proxy_port,
            http_proxy_auth=http_proxy_auth,
        )
      else:
        server.run_forever(
            sslopt={
                'cert_reqs': cert_reqs,
                'ca_certs': ca_certs,
            },
            proxy_type=proxy_type,
        )

    t = threading.Thread(target=Run, daemon=True)
    t.start()

  def _ForwardClientToServer(self, client, server):
    """Forwards data from the client to the server."""
    del self

    def Forward():
      while True:
        try:
          data = client.recv(4096)
          if not data:
            break
          server.send(data)
        except websocket_exceptions.WebSocketConnectionClosedException:
          log.error('Connection to Cloud Shell lost.')
          break
        except (socket.error, websocket_exceptions.WebSocketException) as e:
          log.error('Error forwarding data: %s', e, exc_info=True)
          break
      client.close()

    t = threading.Thread(target=Forward, daemon=True)
    t.start()

  def _OnWebsocketError(self, client, error):
    """Handles WebSocket errors."""
    del self
    if not isinstance(
        error, websocket_exceptions.WebSocketConnectionClosedException
    ):
      log.error('Error connecting to Cloud Shell: %s', error, exc_info=True)
    client.close()
