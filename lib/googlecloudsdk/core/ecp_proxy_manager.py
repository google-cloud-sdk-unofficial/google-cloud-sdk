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
"""Manager for starting and stopping the local ECP HTTP Proxy."""

import atexit
import os
import secrets
import socket
import subprocess
import time
from typing import Optional

from googlecloudsdk.core import context_aware
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import encoding

_CLOUDSDK_ECP_HTTP_PROXY_PORT = 'CLOUDSDK_ECP_HTTP_PROXY_PORT'
_ECP_HTTP_PROXY_MANAGER_INSTANCE = None


class ECPProxyError(Exception):
  """Custom exception for errors related to the ECP proxy communication."""

  def __init__(self, message, original_exception=None):
    self.original_exception = original_exception
    super().__init__(
        f'{message}: {original_exception}' if original_exception else message
    )


def _find_free_port() -> int:
  """Dynamically finds and returns an available TCP port."""
  with socket.socket() as s:
    s.bind(('', 0))
    return s.getsockname()[1]


class _ECPHTTPProxyManager(object):
  """Manages the lifecycle of a local ECP HTTP proxy process."""

  def __init__(
      self, certificate_config_file_path: str, startup_timeout: int = 5
  ):
    self.certificate_config_file_path = certificate_config_file_path
    self.proxy_process = None
    self.proxy_host = 'localhost'
    self.nonce_token = secrets.token_hex(16)
    self.startup_timeout = startup_timeout

    # pylint:disable=g-import-not-at-top
    from googlecloudsdk.core import requests as core_requests

    self.gcloud_proxy_url = core_requests.GetProxyInfo()

    # Register a cleanup function to terminate the proxy process on exit.
    atexit.register(self.close)

    self.proxy_port = self._start_ecp_proxy_with_retries(
        self.startup_timeout, max_retries=1
    )
    encoding.SetEncodedValue(
        os.environ, _CLOUDSDK_ECP_HTTP_PROXY_PORT, str(self.proxy_port)
    )

  def _start_ecp_proxy_with_retries(
      self, timeout: int, max_retries: int = 1
  ) -> int:
    """Attempts to start the ECP Proxy, retrying on failure."""
    cert_config = context_aware.GetCertificateConfig(
        self.certificate_config_file_path
    )
    ecp_http_proxy = cert_config.get('libs', {}).get('ecp_http_proxy')
    if not ecp_http_proxy:
      raise ECPProxyError(
          'ECP HTTP proxy binary path is not specified in enterprise'
          ' certificate config file. Cannot use mTLS with ECP if the ECP HTTP'
          ' proxy binary does not exist. Please check the ECP configuration.'
          ' See `gcloud topic client-certificate` to learn more about ECP. \nIf'
          ' this error is unexpected either delete {} or generate a new'
          ' configuration with `$ gcloud auth enterprise-certificate-config'
          ' create --help` '.format(self.certificate_config_file_path)
      )

    for attempt in range(max_retries + 1):
      proxy_port = _find_free_port()
      self._start_ecp_proxy(
          ecp_http_proxy=ecp_http_proxy, proxy_port=proxy_port
      )

      try:
        self._wait_for_proxy(proxy_port=proxy_port, timeout=timeout)
        return proxy_port
      except ECPProxyError as e:
        if self.proxy_process and self.proxy_process.poll() is None:
          self.proxy_process.terminate()
        if attempt < max_retries:
          log.debug(f'ECP proxy failed to start on port {proxy_port}: {e}')
          continue
        log.debug(f'ECP proxy failed to start after {max_retries} retries: {e}')
        raise

  def _start_ecp_proxy(self, *, ecp_http_proxy: str, proxy_port: int) -> None:
    """Launches the local ECP proxy executable as a subprocess."""
    log.debug(f'Starting local ECP proxy server on port {proxy_port}')

    args = [
        '-enterprise_certificate_file_path',
        self.certificate_config_file_path,
        '-port',
        str(proxy_port),
        '-nonce_token',
        self.nonce_token,
    ]

    if self.gcloud_proxy_url:
      args.extend(
          ['-gcloud_configured_upstream_proxy_url', self.gcloud_proxy_url]
      )

    proxy_args = execution_utils.ArgsForExecutableTool(ecp_http_proxy, *args)
    try:
      self.proxy_process = subprocess.Popen(
          proxy_args,
          stdout=None,
          stderr=None,
      )
    except (OSError, ValueError) as e:
      log.debug(f'Failed to start ECP proxy executable: {e}')
      raise ECPProxyError(
          'Failed to start ECP proxy process', original_exception=e
      ) from e

  def _wait_for_proxy(self, *, proxy_port: int, timeout: int) -> None:
    """Waits for the proxy to become available and verifies its identity."""
    log.debug(f'Waiting for the proxy to be ready on port {proxy_port}...')
    if self.proxy_process is None:
      raise ECPProxyError('Proxy process has not been started.')

    start_time = time.monotonic()

    while time.monotonic() - start_time < timeout:
      if self.proxy_process.poll() is not None:
        raise ECPProxyError(
            'Proxy process terminated unexpectedly with code '
            f'{self.proxy_process.returncode} while waiting for it to start.'
        )

      try:
        with socket.create_connection(
            (self.proxy_host, proxy_port), timeout=0.1
        ):
          break
      except OSError:
        time.sleep(0.1)
        continue
    else:
      self.close()
      raise ECPProxyError(
          f'ECP Proxy on {self.proxy_host}:{proxy_port} did not become ready in'
          f' {timeout} seconds.'
      )

    try:
      # pylint:disable=g-import-not-at-top
      # local import to avoid circular dependency
      import requests as pip_requests

      readyz_url = f'http://{self.proxy_host}:{proxy_port}/readyz'
      response = pip_requests.get(readyz_url, timeout=1)
      if response.status_code != 200:
        raise ECPProxyError(
            f'Proxy /readyz endpoint returned status {response.status_code}.'
        )

      server_nonce = response.text
      if server_nonce != self.nonce_token:
        raise ECPProxyError('Nonce mismatch from proxy /readyz endpoint.')

      log.debug('Proxy is ready and nonce verified.')
    except Exception as e:
      raise ECPProxyError(
          'Failed to verify proxy readiness via /readyz endpoint.',
          original_exception=e,
      ) from e

  def close(self):
    """Terminates the background ECP proxy process to clean up resources."""
    log.debug('Closing ECP Proxy Adapter and terminating proxy process...')
    if self.proxy_process and self.proxy_process.poll() is None:
      self.proxy_process.terminate()
      try:
        self.proxy_process.wait(timeout=0.5)
      except subprocess.TimeoutExpired:
        log.debug('Proxy process did not terminate gracefully, killing it.')
        self.proxy_process.kill()


def get_proxy_port() -> Optional[int]:
  """Retrieves the local ECP HTTP Proxy port, starting it if required.

  If the proxy is already running (either initiated by a previous call or a
  parent process), this function immediately returns the cached port from
  the environment variable without spawning any new processes.

  If the proxy is not running, it evaluates the context-aware configuration to
  determine if an enterprise mTLS certificate offloading proxy is required.
  If required, it synchronously spawns the proxy subprocess, blocks to perform
  security nonce and readiness verification checks, and returns the bound TCP
  port once the server is fully ready.

  Returns:
    Optional[int]: The local TCP port of the running ECP HTTP Proxy server,
      or None if ECP proxy offloading is not required by configuration or
      fails to start.
  """
  global _ECP_HTTP_PROXY_MANAGER_INSTANCE

  # If the port is already set, the proxy was started by a parent process or
  # a previous call.
  port_str = encoding.GetEncodedValue(os.environ, _CLOUDSDK_ECP_HTTP_PROXY_PORT)
  if port_str:
    try:
      return int(port_str)
    except ValueError:
      pass

  # Start the local proxy server if mTLS settings require it.
  try:
    ca_config = context_aware.Config()
  except (
      context_aware.CertProvisionException,
      context_aware.ConfigException,
  ) as e:
    log.debug('Failed to load context-aware configuration: %s', e)
    return None

  if (
      ca_config
      and ca_config.config_type
      == context_aware.ConfigType.ENTERPRISE_CERTIFICATE
      and ca_config.use_local_proxy
  ):
    if _ECP_HTTP_PROXY_MANAGER_INSTANCE is None:
      try:
        _ECP_HTTP_PROXY_MANAGER_INSTANCE = _ECPHTTPProxyManager(
            certificate_config_file_path=ca_config.certificate_config_file_path
        )
      except ECPProxyError as e:
        log.error(f'Failed to start ECP HTTP Proxy: {e}')

    if _ECP_HTTP_PROXY_MANAGER_INSTANCE:
      return _ECP_HTTP_PROXY_MANAGER_INSTANCE.proxy_port

  return None
