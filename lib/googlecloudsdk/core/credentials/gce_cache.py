# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Caching logic for checking if we are on Google Compute Engine (GCE).

This module checks if gcloud runs on a GCE virtual machine. The check sends an
HTTP GET request to the GCE metadata server. Because HTTP requests are slow and
can fail during startup, this module caches the residency result in memory and
on disk for 10 minutes.

To prevent authentication failures and latency regressions across different
environments, the caching and retry logic obeys these rules:
1. SMBIOS check: Before HTTP probing, the module checks Linux kernel DMI
   files (/sys/class/dmi/id/...) or Windows registry SMBIOS information as a
   residency heuristic.
2. Adaptive retry budget:
   a. If SMBIOS indicates GCE, HTTP metadata probes allow 5 retries (6 total
      attempts) to handle startup delays and proxy initialization.
   b. If SMBIOS does not indicate GCE or is unreadable, HTTP metadata probes
      allow 3 retries (4 total attempts).
3. Selective backoff:
   a. HTTP 429 (Too Many Requests) and 503 (Service Unavailable) errors use an
      exponential backoff delay between retries to allow metadata proxy queues
      to drain.
   b. Socket timeouts and connection errors retry immediately without adding
      extra backoff sleep on top of the probe socket timeout.
4. Consistent disk caching: The module writes the residency result to disk for
   10 minutes across all paths to prevent repeated checks.

For more information on GCE residency detection, see:
https://cloud.google.com/compute/docs/instances/detect-compute-engine
"""

import http.client
import os
import socket
import threading
import time
import urllib.error

from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import gce_read
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import retry

SslCertificateError = None  # pylint: disable=invalid-name
try:
  import ssl  # pylint: disable=g-import-not-at-top
except ImportError:
  pass
if ssl is not None:
  SslCertificateError = getattr(ssl, 'CertificateError', None)

_GCE_CACHE_MAX_AGE = 10 * 60  # 10 minutes
_GCE_SMBIOS_MAX_RETRIALS = 5
_DEFAULT_MAX_RETRIALS = 3
_HTTP_ERROR_INITIAL_SLEEP_SEC = 0.5
_HTTP_ERROR_EXPONENTIAL_SLEEP_MULTIPLIER = 1.5
_BACKOFF_HTTP_ERROR_CODES = (429, 503)

# Depending on how a firewall/ NAT behaves, we can have different
# exceptions at different levels in the networking stack when trying to
# access an address that we can't reach. Capture all these exceptions.
_POSSIBLE_ERRORS_GCE_METADATA_CONNECTION = (
    urllib.error.URLError,
    socket.error,
    http.client.HTTPException,
    SslCertificateError,
)


def _ShouldRetryMetadataServerConnection(exc_type, exc_value, exc_traceback,
                                         state):
  """Decides if we need to retry the metadata server connection."""
  del exc_type, exc_traceback, state
  if not isinstance(exc_value, _POSSIBLE_ERRORS_GCE_METADATA_CONNECTION):
    return False
  if isinstance(exc_value, urllib.error.URLError) and isinstance(
      exc_value.reason, socket.gaierror
  ):
    return False

  return True


def _GetMetadataServerSleepMs(exc_type, exc_value, exc_traceback, state):
  """Calculates sleep time in ms for retriable metadata server HTTP errors."""
  del exc_type, exc_traceback
  if isinstance(exc_value, urllib.error.HTTPError):
    if exc_value.code in _BACKOFF_HTTP_ERROR_CODES:
      retrial = state.retrial if state is not None else 0
      sleep_sec = _HTTP_ERROR_INITIAL_SLEEP_SEC * (
          _HTTP_ERROR_EXPONENTIAL_SLEEP_MULTIPLIER**retrial
      )
      return int(sleep_sec * 1000)
  return 0


class _OnGCECache(object):
  """Logic to check if we're on GCE and cache the result to file or memory.

  Checking if we are on GCE is done by issuing an HTTP request to a GCE server.
  Since HTTP requests are slow, we cache this information. Because every run
  of gcloud is a separate command, the cache is stored in a file in the user's
  gcloud config dir. Because within a gcloud run we might check if we're on GCE
  multiple times, we also cache this information in memory.
  A user can move the gcloud instance to and from a GCE VM, and the GCE server
  can sometimes not respond. Therefore the cache has an age and gets refreshed
  if more than _GCE_CACHE_MAX_AGE passed since it was updated.
  """

  def __init__(self, connected=None, expiration_time=None, gce_cache_path=None):
    self.connected = connected
    self.expiration_time = expiration_time
    self.file_lock = threading.Lock()
    self._gce_cache_path = gce_cache_path

  def _GetGCECachePath(self):
    return self._gce_cache_path or config.Paths().GCECachePath()

  def GetOnGCE(self, check_age=True):
    """Check if we are on a GCE machine.

    Checks, in order:
    * in-memory cache
    * on-disk cache
    * metadata server

    If we read from one of these sources, update all of the caches above it in
    the list.

    If check_age is True, then update all caches if the information we have is
    older than _GCE_CACHE_MAX_AGE. In most cases, age should be respected. It
    was added for reporting metrics.

    Args:
      check_age: bool, determines if the cache should be refreshed if more than
        _GCE_CACHE_MAX_AGE time passed since last update.

    Returns:
      bool, if we are on GCE or not.
    """
    on_gce = self._CheckMemory(check_age=check_age)
    if on_gce is not None:
      log.debug('On GCE from memory cache: %s', on_gce)
      return on_gce

    self._WriteMemory(*self._CheckDisk())
    on_gce = self._CheckMemory(check_age=check_age)
    if on_gce is not None:
      log.debug('On GCE from disk cache: %s', on_gce)
      return on_gce

    return self.CheckServerRefreshAllCaches()

  def _IsGceSmbios(self):
    """Checks if SMBIOS data indicates a Google Compute Engine host.

    Returns:
      bool, True if Linux DMI sysfs or Windows registry SMBIOS data indicates
      Google, False otherwise.
    """
    if os.name == 'nt':
      return self._IsGceSmbiosWindows()
    return self._IsGceSmbiosLinux()

  def _IsGceSmbiosWindows(self):
    """Checks Windows registry SMBIOS information for GCE residency."""
    try:
      from six.moves import winreg  # pylint: disable=g-import-not-at-top

      with winreg.OpenKey(
          winreg.HKEY_LOCAL_MACHINE,
          r'HARDWARE\DESCRIPTION\System\BIOS',
      ) as key:
        manufacturer, _ = winreg.QueryValueEx(key, 'SystemManufacturer')
        product_name, _ = winreg.QueryValueEx(key, 'SystemProductName')
        if 'Google' in str(manufacturer) or 'Google' in str(product_name):
          return True
    except (ImportError, OSError, IOError, AttributeError):
      pass
    return False

  def _IsGceSmbiosLinux(self):
    """Checks Linux sysfs DMI files for GCE residency via google-auth."""
    try:
      from google.auth import compute_engine  # pylint: disable=g-import-not-at-top

      return compute_engine.detect_gce_residency_linux()
    except (ImportError, AttributeError):
      return False

  def CheckServerRefreshAllCaches(self):
    """Checks the metadata server and refreshes all caches.

    This method checks SMBIOS data inside _CheckServer to set the retry budget
    for HTTP probes. It writes the residency result to disk and memory for 10
    minutes.

    Returns:
      bool, True if running on GCE, False otherwise.
    """
    try:
      on_gce = self._CheckServer()
      log.debug('On GCE from server: %s', on_gce)
    except _POSSIBLE_ERRORS_GCE_METADATA_CONNECTION as e:  # pylint: disable=catching-non-exception
      log.debug('Failed to check metadata server: %s', e)
      on_gce = False

    self._WriteDisk(on_gce)
    self._WriteMemory(on_gce, time.time() + _GCE_CACHE_MAX_AGE)
    return on_gce

  def _CheckMemory(self, check_age):
    if not check_age:
      return self.connected
    if self.expiration_time and self.expiration_time >= time.time():
      return self.connected
    return None

  def _WriteMemory(self, on_gce, expiration_time):
    self.connected = on_gce
    self.expiration_time = expiration_time

  def _CheckDisk(self):
    """Reads cache from disk."""
    gce_cache_path = self._GetGCECachePath()
    with self.file_lock:
      try:
        mtime = os.stat(gce_cache_path).st_mtime
        expiration_time = mtime + _GCE_CACHE_MAX_AGE
        gcecache_file_value = files.ReadFileContents(gce_cache_path)
        return gcecache_file_value == str(True), expiration_time
      except (OSError, IOError, files.Error) as e:
        # Failed to read Google Compute Engine credential cache file.
        # This could be due to permission reasons, or because it doesn't yet
        # exist.
        log.debug('Failed to read GCE cache file: %s', e)
        return None, None

  def _WriteDisk(self, on_gce):
    """Updates cache on disk."""
    gce_cache_path = self._GetGCECachePath()
    with self.file_lock:
      try:
        files.WriteFileContents(gce_cache_path, str(on_gce), private=True)
      except (OSError, IOError, files.Error) as e:
        # Failed to write Google Compute Engine credential cache file.
        # This could be due to permission reasons, or because it doesn't yet
        # exist.
        log.debug('Failed to write GCE cache file: %s', e)

  def _CheckServer(self, max_retrials=None):
    """Probes the metadata server with retries.

    Args:
      max_retrials: int or None, maximum number of total attempts on connection
        error. If None, set dynamically based on SMBIOS residency checks.

    Returns:
      bool, True if the metadata server responds with a numeric project ID.
    """
    if max_retrials is None:
      max_retrials = (
          _GCE_SMBIOS_MAX_RETRIALS
          if self._IsGceSmbios()
          else _DEFAULT_MAX_RETRIALS
      )

    @retry.RetryOnException(
        max_retrials=max_retrials,
        should_retry_if=_ShouldRetryMetadataServerConnection,
        sleep_ms=_GetMetadataServerSleepMs,
    )
    def _TryCheckServer():
      return gce_read.ReadNoProxy(
          gce_read.GOOGLE_GCE_METADATA_NUMERIC_PROJECT_URI,
          properties.VALUES.compute.gce_metadata_check_timeout_sec.GetInt(),
      ).isdigit()

    return _TryCheckServer()


# Since a module is initialized only once, this is effective a singleton
_SINGLETON_ON_GCE_CACHE = _OnGCECache()


def GetOnGCE(check_age=True, gce_cache_instance=None):
  """Helper function to abstract the caching logic of if we're on GCE."""
  gce_cache_instance = gce_cache_instance or _SINGLETON_ON_GCE_CACHE
  return gce_cache_instance.GetOnGCE(check_age)


def ForceCacheRefresh(gce_cache_instance=None):
  """Force rechecking server status and refreshing of all the caches."""
  gce_cache_instance = gce_cache_instance or _SINGLETON_ON_GCE_CACHE
  return gce_cache_instance.CheckServerRefreshAllCaches()
