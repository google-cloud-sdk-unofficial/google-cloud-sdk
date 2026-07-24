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
"""Caching logic for checking if we're on GCE."""


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

  def CheckServerRefreshAllCaches(self):
    """Checks the metadata server and refreshes all caches."""
    try:
      on_gce = self._CheckServer()
      log.debug('On GCE from server: %s', on_gce)
      self._WriteDisk(on_gce)
    except _POSSIBLE_ERRORS_GCE_METADATA_CONNECTION as e:  # pylint: disable=catching-non-exception
      log.debug('Failed to check metadata server: %s', e)
      # Only write False to disk if the error is a definitive DNS failure
      # (socket.gaierror).  Transient connection errors (e.g., refused/timeout)
      # are not written to disk to prevent cache poisoning during startup races
      # (see b/529362127).
      if isinstance(e, urllib.error.URLError) and isinstance(
          e.reason, socket.gaierror
      ):
        self._WriteDisk(False)
      on_gce = False

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

  @retry.RetryOnException(
      max_retrials=3,
      should_retry_if=_ShouldRetryMetadataServerConnection,
      sleep_ms=500,
      exponential_sleep_multiplier=2,
  )
  def _CheckServer(self):
    return gce_read.ReadNoProxy(
        gce_read.GOOGLE_GCE_METADATA_NUMERIC_PROJECT_URI,
        properties.VALUES.compute.gce_metadata_check_timeout_sec.GetInt(),
    ).isdigit()


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
