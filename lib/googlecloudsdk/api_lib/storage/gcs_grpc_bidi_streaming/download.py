# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Download workflow used by GCS gRPC bidi streaming client."""

from __future__ import annotations

import binascii
import io
import queue
import threading
from typing import Any, Callable, Generator, NamedTuple, Optional, Tuple

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as cloud_errors
from googlecloudsdk.api_lib.storage import gcs_download
from googlecloudsdk.api_lib.storage.gcs_grpc import grpc_util
from googlecloudsdk.api_lib.storage.gcs_grpc import retry_util as grpc_retry_util
from googlecloudsdk.api_lib.storage.gcs_grpc_bidi_streaming import retry_util
from googlecloudsdk.command_lib.storage import errors as storage_errors
from googlecloudsdk.command_lib.storage import fast_crc32c_util
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.util import crc32c
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class BidiDownloadIncompleteError(cloud_errors.RetryableApiError):
  """Raised when BiDi download is incomplete and should be retried."""


# read_id is hardcoded to 1 for simple downloads as we only have one range.
ONE_SHOT_READ_ID = 1


def _get_bidi_read_object_spec(
    gapic_client,
    cloud_resource,
    decryption_key,
    bucket_name,
    read_handle=None,
):
  """Returns a bidi read object spec."""
  bidi_read_object_spec = gapic_client.types.BidiReadObjectSpec(
      bucket=bucket_name,
      object_=cloud_resource.storage_url.resource_name,
      generation=(
          int(cloud_resource.generation) if cloud_resource.generation else None
      ),
      common_object_request_params=grpc_util.get_encryption_request_params(
          gapic_client, decryption_key
      ),
  )
  if read_handle:
    bidi_read_object_spec.read_handle = read_handle
  return bidi_read_object_spec


def _get_bidi_read_range(
    gapic_client, start_byte, end_byte,
):
  """Returns a bidi read range."""
  # A read_length of 0 means read until the end of the object.
  read_length = (
      end_byte - start_byte + 1
      if end_byte is not None
      else 0
  )

  return gapic_client.types.ReadRange(
      read_offset=start_byte,
      read_length=read_length,
      read_id=ONE_SHOT_READ_ID,
  )


def _get_bidi_read_object_request(
    gapic_client,
    cloud_resource,
    start_byte,
    end_byte,
    decryption_key,
    read_handle=None,
):
  """Returns a bidi read object RPC request."""
  bucket_name = grpc_util.get_full_bucket_name(
      cloud_resource.storage_url.bucket_name
  )

  read_object_spec = _get_bidi_read_object_spec(
      gapic_client, cloud_resource, decryption_key, bucket_name, read_handle
  )

  read_range = _get_bidi_read_range(gapic_client, start_byte, end_byte)

  return gapic_client.types.BidiReadObjectRequest(
      read_object_spec=read_object_spec,
      read_ranges=[read_range],
  )


def _update_digesters(digesters, data, chunk_crc32c=None):
  """Updates digesters with data."""
  if digesters is None or chunk_crc32c is None:
    return
  if hash_util.HashAlgorithm.CRC32C not in digesters or isinstance(
      digesters[hash_util.HashAlgorithm.CRC32C],
      fast_crc32c_util.DeferredCrc32c,
  ):
    return

  final_crc32c = crc32c.concat_checksums(
      int.from_bytes(digesters[hash_util.HashAlgorithm.CRC32C].digest(), 'big'),
      chunk_crc32c,
      len(data),
  )
  if isinstance(
      digesters[hash_util.HashAlgorithm.CRC32C],
      fast_crc32c_util.OnTheFlyCrc32c,
  ):
    digesters[hash_util.HashAlgorithm.CRC32C] = fast_crc32c_util.OnTheFlyCrc32c(
        final_crc32c
    )
    return
  digesters[hash_util.HashAlgorithm.CRC32C] = crc32c.get_crc32c_from_checksum(
      final_crc32c
  )


def _should_validate_chunk_integrity(digesters):
  """Returns true if chunk integrity should be validated."""
  if not digesters:
    return False
  if hash_util.HashAlgorithm.CRC32C not in digesters:
    return False
  hash_object = digesters[hash_util.HashAlgorithm.CRC32C]
  if isinstance(hash_object, fast_crc32c_util.DeferredCrc32c):
    return False
  return True


def _validate_chunk_integrity(crc32c_hash, data):
  """Validates integrity of a single chunk by comparing CRC32C hashes.

  If there is a mismatch, it raises HashMismatchError. This error
  is not retried by download retry logic, and will cause the download to fail.
  The download task runner is responsible for deleting partially downloaded
  files in case of such failures.

  Args:
    crc32c_hash (int): The server-provided CRC32C hash of the chunk.
    data (bytes): The chunk data.

  Returns:
    int: The calculated CRC32C checksum if validation is successful.
    None: If chunk validation could not be performed due to an unexpected
      exception.

  Raises:
    storage_errors.HashMismatchError: If chunk integrity check fails.
  """
  log.debug('Validating chunk integrity for CRC32C: %s', crc32c_hash)
  try:
    # Partial CRC32C calculation is done only if google_crc32c is present or if
    # streaming download is used.
    hasher = fast_crc32c_util.get_crc32c(is_streaming=True)
    hasher.update(data)
    calculated_crc32c = crc32c.get_checksum(hasher)
    if crc32c_hash != calculated_crc32c:
      expected_bytes = crc32c_hash.to_bytes(4, byteorder='big')
      calculated_bytes = calculated_crc32c.to_bytes(4, byteorder='big')
      log.error(
          'Mismatch for chunk! Expected CRC32C: %s (%s), Actual CRC32C: %s'
          ' (%s).',
          crc32c_hash,
          binascii.hexlify(expected_bytes),
          calculated_crc32c,
          binascii.hexlify(calculated_bytes),
      )
      raise storage_errors.HashMismatchError(
          'Transferred chunk CRC32C does not match.'
      )
    return calculated_crc32c
  except storage_errors.HashMismatchError:
    raise
  except Exception as e:  # pylint: disable=broad-except
    log.debug('Could not perform chunk validation for CRC32C: %s', e)
    # If we can't validate the chunk, we should continue the download without
    # failing the entire operation.
    return None


def _process_data_from_bidi_read_object_rpc(
    gapic_client,
    cloud_resource,
    download_stream,
    digesters,
    progress_callback,
    start_byte,
    end_byte,
    download_strategy,
    decryption_key,
    redirection_handler,
    read_handle=None,
):
  """Receives data from the bidi read object RPC."""
  bidi_read_object_request = _get_bidi_read_object_request(
      gapic_client,
      cloud_resource,
      start_byte,
      end_byte,
      decryption_key,
      read_handle,
  )
  bidi_read_object_rpc = (
      redirection_handler.start_bidi_rpc_with_retry_on_redirected_token_error(
          bidi_read_object_request
      )
  )
  processed_bytes = start_byte
  destination_pipe_is_broken = False
  received_read_handle = read_handle
  try:
    bidi_read_object_rpc.requests_done()

    while bidi_read_object_rpc.is_active:
      try:
        bidi_read_object_response = bidi_read_object_rpc.recv()
        if (
            bidi_read_object_response
            and bidi_read_object_response.read_handle
            and bidi_read_object_response.read_handle.handle
        ):
          received_read_handle = bidi_read_object_response.read_handle
      except (StopIteration, EOFError):
        break
      except Exception as exc_value:  # pylint: disable=broad-except
        if grpc_retry_util.is_retriable(exc_value=exc_value):
          log.debug(
              'Retriable error during bidi_read_object_rpc.recv(): %s',
              exc_value,
          )
          break
        raise
      else:
        # This block executes only if the try block completes without an
        # exception.
        for object_range_data in bidi_read_object_response.object_data_ranges:
          data = object_range_data.checksummed_data.content
          if data:
            chunk_crc32c = None
            if _should_validate_chunk_integrity(digesters):
              chunk_crc32c = _validate_chunk_integrity(
                  object_range_data.checksummed_data.crc32c, data)

            try:
              download_stream.write(data)
            except BrokenPipeError:
              if download_strategy == cloud_api.DownloadStrategy.ONE_SHOT:
                log.info('Writing to download stream raised broken pipe error.')
                destination_pipe_is_broken = True
                break
              raise

            if digesters:
              _update_digesters(digesters, data, chunk_crc32c)

            processed_bytes += len(data)
            if progress_callback:
              progress_callback(processed_bytes)

        if destination_pipe_is_broken:
          break
  finally:
    # Ensures the stream is closed even if an exception is raised.
    bidi_read_object_rpc.close()
  return processed_bytes, destination_pipe_is_broken, received_read_handle


def _get_target_size(cloud_resource, start_byte, end_byte):
  """Returns the target size for the download."""
  if cloud_resource.size is None:
    return None

  target_size = cloud_resource.size
  if end_byte is not None:
    target_size = end_byte - start_byte + 1
  elif start_byte > 0:
    target_size = cloud_resource.size - start_byte
  elif start_byte < 0:
    # It's a suffix read. The target size is the absolute value of start_byte.
    target_size = min(cloud_resource.size, abs(start_byte))

  return target_size


def bidi_download_object(
    gapic_client,
    cloud_resource,
    download_stream,
    digesters,
    progress_callback,
    start_byte,
    end_byte,
    download_strategy,
    decryption_key,
    redirection_handler,
):
  """Downloads the object using gRPC bidi streaming API.

  Args:
    gapic_client (StorageClient): The GAPIC API client to interact with GCS
      using gRPC.
    cloud_resource (resource_reference.ObjectResource): See
      cloud_api.CloudApi.download_object.
    download_stream (stream): Stream to send the object data to.
    digesters (dict): See cloud_api.CloudApi.download_object.
    progress_callback (function): See cloud_api.CloudApi.download_object.
    start_byte (int): Starting point for download (for resumable downloads and
      range requests). Can be set to negative to request a range of bytes
      (python equivalent of [:-3]).
    end_byte (int): Ending byte number, inclusive, for download (for range
      requests). If None, download the rest of the object.
    download_strategy (cloud_api.DownloadStrategy): Download strategy used to
      perform the download.
    decryption_key (encryption_util.EncryptionKey|None): The decryption key to
      be used to download the object if the object is encrypted.
    redirection_handler (retry_util.BidiRedirectedTokenErrorHandler): The
      redirection handler to handle redirected token errors.
  """

  target_size = _get_target_size(cloud_resource, start_byte, end_byte)
  processed_bytes, destination_pipe_is_broken = retry_util.run_with_retries(
      _process_data_from_bidi_read_object_rpc,
      gapic_client,
      cloud_resource,
      download_stream,
      digesters,
      progress_callback,
      start_byte,
      end_byte,
      download_strategy,
      decryption_key,
      target_size,
      redirection_handler,
  )

  total_downloaded_data = processed_bytes - start_byte
  if (
      target_size is not None
      and total_downloaded_data < target_size
      and not destination_pipe_is_broken
  ):
    error_message = (
        'Download not completed for %s. Target size=%s, downloaded data=%s.'
        ' The input stream terminated before the entire content was read,'
        ' possibly due to a network condition.'
    ) % (
        cloud_resource.storage_url.resource_name,
        target_size,
        total_downloaded_data,
    )
    log.debug(error_message)
    raise cloud_errors.RetryableApiError(error_message)

  return None


class BidiDownloader:
  """Helper class to manage state for resumable Bidi downloads."""

  def __init__(
      self,
      process_chunk_func: Callable[..., Tuple[int, bool]],
      gapic_client: 'storage_client_v2.StorageClient',
      cloud_resource: 'resource_reference.ObjectResource',
      download_stream: io.IOBase,
      digesters: dict[str, Any] | None,
      progress_callback: Callable[[int], None] | None,
      start_byte: int,
      end_byte: int | None,
      download_strategy: cloud_api.DownloadStrategy,
      decryption_key: 'encryption_util.EncryptionKey' | None,
      target_size: int | None,
      redirection_handler: retry_util.BidiRedirectedTokenErrorHandler,
  ):
    """Initializes a BidiDownloader instance.

    Args:
      process_chunk_func (Callable[..., Tuple[int, bool]]): Function that
        downloads a chunk of data and returns processed_bytes and
        destination_pipe_is_broken.
      gapic_client (StorageClient): The GAPIC API client to interact with GCS
        using gRPC.
      cloud_resource (resource_reference.ObjectResource): See
        cloud_api.CloudApi.download_object.
      download_stream (io.IOBase): Stream to send the object data to.
      digesters (Dict[str, 'hashlib._Hash'] | None): See
        cloud_api.CloudApi.download_object.
      progress_callback (Callable[[int], None] | None): See
        cloud_api.CloudApi.download_object.
      start_byte (int): Starting point for download.
      end_byte (int | None): Ending byte number, inclusive, for download. If
        None, download the rest of the object.
      download_strategy (cloud_api.DownloadStrategy): Download strategy used to
        perform the download.
      decryption_key (EncryptionKey | None): The decryption key to
        be used to download the object if the object is encrypted.
      target_size (int | None): The total number of bytes to download.
      redirection_handler (retry_util.BidiRedirectedTokenErrorHandler): The
        redirection handler to handle redirected token errors.
    """
    self.process_chunk_func = process_chunk_func
    self.gapic_client = gapic_client
    self.cloud_resource = cloud_resource
    self.download_stream = download_stream
    self.digesters = digesters
    self.progress_callback = progress_callback
    self.start_byte = start_byte
    self.end_byte = end_byte
    self.download_strategy = download_strategy
    self.decryption_key = decryption_key
    self.target_size = target_size
    self.processed_bytes = start_byte
    self.redirection_handler = redirection_handler
    self.destination_pipe_is_broken = False
    self.read_handle = None

  def download_chunk(self):
    """Performs one download attempt and updates processed_bytes.

    If the attempt failed with a retriable error, the download will be
    re-performed from the last processed byte.

    Raises:
      BidiDownloadIncompleteError: If the download stream ends before all bytes
        are received, triggering a retry.

    Returns:
      A tuple containing:
      - int: The total number of bytes processed.
      - bool: True if the destination pipe is broken, False otherwise.
    """
    (
        self.processed_bytes,
        self.destination_pipe_is_broken,
        self.read_handle,
    ) = self.process_chunk_func(
        self.gapic_client,
        self.cloud_resource,
        self.download_stream,
        self.digesters,
        self.progress_callback,
        self.processed_bytes,  # Resume from last processed byte.
        self.end_byte,
        self.download_strategy,
        self.decryption_key,
        self.redirection_handler,
        read_handle=self.read_handle,
    )
    total_downloaded_data = self.processed_bytes - self.start_byte
    if self.destination_pipe_is_broken:
      return self.processed_bytes, self.destination_pipe_is_broken
    if self.target_size is None or total_downloaded_data >= self.target_size:
      # Download complete.
      return self.processed_bytes, self.destination_pipe_is_broken
    raise BidiDownloadIncompleteError('Stream ended prematurely.')


class BidiGrpcDownload(gcs_download.GcsDownload):
  """Perform GCS Download using gRPC bidi streaming API."""

  def __init__(self,
               gapic_client,
               cloud_resource,
               download_stream,
               start_byte,
               end_byte,
               digesters,
               progress_callback,
               download_strategy,
               decryption_key):
    """Initializes a BidiGrpcDownload instance.

    Args:
      gapic_client (StorageClient): The GAPIC API client to interact with
        GCS using gRPC.
      cloud_resource (resource_reference.ObjectResource): See
        cloud_api.CloudApi.download_object.
      download_stream (stream): Stream to send the object data to.
      start_byte (int): See super class.
      end_byte (int): See super class.
      digesters (dict): See cloud_api.CloudApi.download_object.
      progress_callback (function): See cloud_api.CloudApi.download_object.
      download_strategy (cloud_api.DownloadStrategy): Download strategy used to
        perform the download.
      decryption_key (encryption_util.EncryptionKey|None): The decryption key to
        be used to download the object if the object is encrypted.
    """
    super(BidiGrpcDownload, self).__init__(
        download_stream, start_byte, end_byte
    )
    self._gapic_client = gapic_client
    self._cloud_resource = cloud_resource
    self._digesters = digesters
    self._progress_callback = progress_callback
    self._download_strategy = download_strategy
    self._decryption_key = decryption_key
    self._redirection_handler = retry_util.BidiRedirectedTokenErrorHandler(
        self._gapic_client,
        source_resource=self._cloud_resource,
        destination_resource=self._download_stream,
    )

  def should_retry(self, exc_type, exc_value, exc_traceback):
    """See super class."""
    return grpc_retry_util.is_retriable(exc_type, exc_value, exc_traceback)

  def launch(self):
    """See super class."""
    if properties.VALUES.storage.use_mrd_bidi_downloads.GetBool():
      return bidi_download_object_mrd(
          gapic_client=self._gapic_client,
          cloud_resource=self._cloud_resource,
          download_stream=self._download_stream,
          digesters=self._digesters,
          progress_callback=self._progress_callback,
          start_byte=self._start_byte,
          end_byte=self._end_byte,
          download_strategy=self._download_strategy,
          decryption_key=self._decryption_key,
          redirection_handler=self._redirection_handler,
      )
    return bidi_download_object(
        gapic_client=self._gapic_client,
        cloud_resource=self._cloud_resource,
        download_stream=self._download_stream,
        digesters=self._digesters,
        progress_callback=self._progress_callback,
        start_byte=self._start_byte,
        end_byte=self._end_byte,
        download_strategy=self._download_strategy,
        decryption_key=self._decryption_key,
        redirection_handler=self._redirection_handler,
    )

  @grpc_retry_util.grpc_default_retryer
  def simple_download(self):
    """Downloads the object.

    On retriable errors, the entire download will be re-performed instead of
    resuming from a particular byte. This is useful for streaming download
    cases.

    Unlike Apitools, the GAPIC client doesn't retry the request by
    default, hence we are using the decorator.

    Returns:
      Encoding string for object if requested. Otherwise, None.
    """
    return self.launch()

  def run(self):
    """See super class."""
    if self._download_strategy == cloud_api.DownloadStrategy.ONE_SHOT:
      return self.simple_download()
    else:
      return super(BidiGrpcDownload, self).run(retriable_in_flight=True)


class OffsetSequencer:
  """Sequences out-of-order chunks from a multi-range download stream.

  Handles out-of-order chunks and yields contiguous blocks for the decoupled
  writer. Note that the internal buffer is theoretically unbounded; it is the
  responsibility of the client (e.g., via bounded network multiplexing)
  to ensure peak memory is mathematically capped.
  """

  def __init__(self, start_offset: int):
    self._next_expected_offset = start_offset
    self._buffer = {}  # type: dict[int, bytes]

  def add_chunk(
      self, offset: int, data: bytes, expected_crc32c: int | None = None
  ):
    """Caches a chunk of data at the given offset.

    Args:
      offset: The byte offset where this data starts.
      data: The chunk's byte data.
      expected_crc32c: The server-provided CRC32C hash of the chunk.
    """
    if not data:
      return

    # Ignore chunks we've already processed (e.g., retried network ranges).
    if offset < self._next_expected_offset:
      overlap = self._next_expected_offset - offset
      if overlap >= len(data):
        return
      data = data[overlap:]
      expected_crc32c = None
      offset = self._next_expected_offset

    if offset not in self._buffer:
      self._buffer[offset] = (data, expected_crc32c)

  @property
  def next_expected_offset(self) -> int:
    """Returns the next contiguous byte offset expected."""
    return self._next_expected_offset

  def clear(self):
    """Clears the internal cache of out-of-order chunks.

    This must be called when the GRPC stream drops and is retried. It prevents
    stale chunks from a previous dead stream from causing complex overlap
    corruptions or memory leaks if the new stream uses different chunk
    boundaries.
    """
    self._buffer.clear()

  def yield_sequential_chunks(
      self,
  ) -> Generator[tuple[int, bytes, int | None], None, None]:
    """Yields all cached chunks that form a contiguous sequence.

    Yields:
      tuple: Contiguous chunks of data in the form (offset, data,
      expected_crc32c).
    """
    while self._next_expected_offset in self._buffer:
      offset = self._next_expected_offset
      data, expected_crc32c = self._buffer.pop(offset)
      self._next_expected_offset += len(data)
      yield offset, data, expected_crc32c


class AsyncDecoupledWriter:
  """A decoupled thread for writing downloaded chunks to the download stream.

  A consumer thread that pulls from a bounded queue and writes to the stream
  sequentially, avoiding blocking the network ingestion loop.
  """

  def __init__(
      self,
      download_stream: io.IOBase,
      digesters: dict[str, Any] | None = None,
      progress_callback: Callable[[int], None] | None = None,
      start_byte: int = 0,
      max_queue_size: int = 32,
  ):
    self._download_stream = download_stream
    self._digesters = digesters or {}
    self._progress_callback = progress_callback
    self._processed_bytes = start_byte
    self._queue = queue.Queue(maxsize=max_queue_size)
    self._writer_thread = None
    self._stop_event = threading.Event()
    self._exception = None

  @property
  def processed_bytes(self) -> int:
    return self._processed_bytes

  @property
  def is_alive(self) -> bool:
    return self._writer_thread is not None and self._writer_thread.is_alive()

  def start(self):
    """Spawns and starts the background writer thread."""
    if self._writer_thread is not None:
      return
    self._writer_thread = threading.Thread(target=self._worker)
    self._writer_thread.daemon = True
    self._writer_thread.start()

  def write(self, offset: int, data: bytes, expected_crc32c: int | None = None):
    """Adds a chunk of data to the queue to be written to download stream.

    Args:
      offset: The byte offset where the data should be written.
      data: The chunk's byte data.
      expected_crc32c: The expected CRC32C hash of the data.

    Raises:
      Exception: If the background writer thread encountered an error.
      RuntimeError: If the background writer thread is not running.
    """
    if self._writer_thread is None:
      raise RuntimeError('Writer thread was never started.')

    while True:
      if self._exception:
        raise self._exception
      if not self._writer_thread.is_alive():
        raise RuntimeError('Writer thread died unexpectedly.')

      try:
        self._queue.put((offset, data, expected_crc32c), timeout=0.1)
        break
      except queue.Full:
        continue

  def _worker(self):
    """Background thread worker that processes the queue.

    This thread safely handles disk I/O, streaming integrity hashing, and
    progress reporting. By executing these tasks here, we offload the CPU
    and I/O bounds from the main network ingestion loop.
    """
    is_seekable = False
    try:
      is_seekable = self._download_stream.seekable()
    except Exception:  # pylint: disable=broad-except
      pass

    # We track expected offset for non-seekable streams and hashes.
    next_expected_offset = None

    while not self._stop_event.is_set() or not self._queue.empty():
      try:
        # Tuple unpacking for future-proofing out-of-order sparse writes
        offset, data, expected_crc32c = self._queue.get(timeout=0.1)
      except queue.Empty:
        continue

      try:
        if next_expected_offset is not None and offset != next_expected_offset:
          if not is_seekable:
            raise IOError(
                'Stream is not seekable and received out-of-order data. '
                'Data must be sequenced before writing to non-seekable streams.'
            )
          if self._digesters:
            raise IOError(
                'Cannot compute streaming hashes securely on out-of-order data.'
            )

        if is_seekable:
          self._download_stream.seek(offset)

        chunk_crc32c = None
        if expected_crc32c is not None or _should_validate_chunk_integrity(
            self._digesters
        ):
          if expected_crc32c is not None:
            chunk_crc32c = _validate_chunk_integrity(expected_crc32c, data)
          else:
            hasher = fast_crc32c_util.get_crc32c(is_streaming=True)
            hasher.update(data)
            chunk_crc32c = crc32c.get_checksum(hasher)

        self._download_stream.write(data)
        self._processed_bytes += len(data)
        next_expected_offset = offset + len(data)

        if self._digesters:
          _update_digesters(self._digesters, data, chunk_crc32c)

        if self._progress_callback:
          self._progress_callback(self._processed_bytes)

      except Exception as e:  # pylint: disable=broad-except
        log.debug(
            'AsyncDecoupledWriter thread %s encountered an error: %s',
            threading.current_thread().name,
            e,
        )
        self._exception = e
        break
      finally:
        self._queue.task_done()

  def stop(self):
    """Stops the writer thread, waits for it to drain, and raises any errors.

    Raises:
      Exception: If the background writer thread encountered an error.
    """
    self._stop_event.set()
    if self._writer_thread and self._writer_thread.is_alive():
      self._writer_thread.join()
    if self._exception:
      raise self._exception


def bidi_download_object_mrd(
    gapic_client: Any,
    cloud_resource: Any,
    download_stream: Any,
    digesters: dict[hash_util.HashAlgorithm, hash_util.HashObject],
    progress_callback: Any,
    start_byte: int,
    end_byte: Optional[int],
    download_strategy: cloud_api.DownloadStrategy,
    decryption_key: Optional[bytes],
    redirection_handler: Any,
) -> None:
  """Optimized Bidi download using Multi-Range Request and Decoupled Writer.

  Args:
    gapic_client: The GAPIC API client to interact with GCS using gRPC.
    cloud_resource: See cloud_api.CloudApi.download_object.
    download_stream: Stream to send the object data to.
    digesters: See cloud_api.CloudApi.download_object.
    progress_callback: See cloud_api.CloudApi.download_object.
    start_byte: Starting point for download.
    end_byte: Ending byte number, inclusive, for download.
    download_strategy: Download strategy used to perform the download.
    decryption_key: The decryption key to be used to download the object.
    redirection_handler: The redirection handler for token errors.

  Returns:
    None
  """
  target_size = _get_target_size(cloud_resource, start_byte, end_byte)
  if properties.VALUES.storage.preallocate_disk_space.GetBool():
    alloc_start_byte = start_byte
    # Translate suffix reads to absolute offsets if the object size is known
    if start_byte < 0 and getattr(cloud_resource, 'size', None) is not None:
      alloc_start_byte = max(0, cloud_resource.size + start_byte)

    # Only preallocate if we have a valid, non-negative absolute offset
    if alloc_start_byte >= 0:
      posix_util.preallocate_disk_space(
          download_stream, alloc_start_byte, target_size
      )
  processed_bytes, destination_pipe_is_broken = retry_util.run_with_retries(
      _process_data_from_mrd_rpc,
      gapic_client,
      cloud_resource,
      download_stream,
      digesters,
      progress_callback,
      start_byte,
      end_byte,
      download_strategy,
      decryption_key,
      target_size,
      redirection_handler,
  )

  total_downloaded_data = processed_bytes - start_byte
  if (
      target_size is not None
      and total_downloaded_data < target_size
      and not destination_pipe_is_broken
  ):
    error_message = (
        'Download not completed for %s. Target size=%s, downloaded data=%s.'
        ' The input stream terminated before the entire content was read,'
        ' possibly due to a network condition.'
    ) % (
        cloud_resource.storage_url.resource_name,
        target_size,
        total_downloaded_data,
    )
    log.debug(error_message)
    raise cloud_errors.RetryableApiError(error_message)

  return None


_OPTIMIZED_CHUNK_SIZE = 32 * 1024 * 1024
_OPTIMIZED_MAX_IN_FLIGHT = 4


def _calculate_mrd_ranges_to_send(
    gapic_client: Any,
    start_byte: int,
    end_byte: int | None,
    cloud_resource: Any,
) -> list[Any]:
  """Calculates all ReadRange segments needed for MRD."""
  ranges_to_send = []
  if end_byte is not None:
    final_byte = end_byte
  elif cloud_resource.size is not None and cloud_resource.size > 0:
    final_byte = cloud_resource.size - 1
  elif cloud_resource.size == 0:
    return ranges_to_send
  else:
    # Size is missing and end_byte is not provided.
    # Yield a single range to read until the end of the object.
    ranges_to_send.append(
        gapic_client.types.ReadRange(
            read_offset=start_byte,
            read_length=0,
            read_id=1,
        )
    )
    return ranges_to_send

  current_offset = start_byte
  read_id = 1
  while current_offset <= final_byte:
    length = min(_OPTIMIZED_CHUNK_SIZE, final_byte - current_offset + 1)
    ranges_to_send.append(
        gapic_client.types.ReadRange(
            read_offset=current_offset,
            read_length=length,
            read_id=read_id,
        )
    )
    current_offset += length
    read_id += 1
  return ranges_to_send


class _MrdRpcResult(NamedTuple):
  processed_bytes: int
  destination_pipe_is_broken: bool
  received_read_handle: Any


def _process_data_from_mrd_rpc(
    gapic_client: Any,
    cloud_resource: Any,
    download_stream: Any,
    digesters: dict[hash_util.HashAlgorithm, hash_util.HashObject],
    progress_callback: Any,
    start_byte: int,
    end_byte: Optional[int],
    download_strategy: cloud_api.DownloadStrategy,
    decryption_key: Optional[bytes],
    redirection_handler: Any,
    read_handle: Any = None,
) -> _MrdRpcResult:
  """Constructs ranges and receives data from the bidi read object RPC using Multi-Range Requests."""
  bucket_name = grpc_util.get_full_bucket_name(
      cloud_resource.storage_url.bucket_name
  )
  read_object_spec = _get_bidi_read_object_spec(
      gapic_client, cloud_resource, decryption_key, bucket_name, read_handle
  )

  ranges_to_send = _calculate_mrd_ranges_to_send(
      gapic_client, start_byte, end_byte, cloud_resource
  )

  initial_ranges = ranges_to_send[:_OPTIMIZED_MAX_IN_FLIGHT]
  ranges_to_send = ranges_to_send[_OPTIMIZED_MAX_IN_FLIGHT:]

  initial_request = gapic_client.types.BidiReadObjectRequest(
      read_object_spec=read_object_spec,
      read_ranges=initial_ranges,
  )

  bidi_read_object_rpc = (
      redirection_handler.start_bidi_rpc_with_retry_on_redirected_token_error(
          initial_request
      )
  )

  if not ranges_to_send:
    bidi_read_object_rpc.requests_done()

  sequencer = OffsetSequencer(start_byte)
  writer = AsyncDecoupledWriter(
      download_stream=download_stream,
      digesters=digesters,
      progress_callback=progress_callback,
      start_byte=start_byte,
  )
  success = False
  try:
    writer.start()

    received_read_handle, destination_pipe_is_broken = (
        _handle_mrd_bidi_responses(
            gapic_client,
            bidi_read_object_rpc,
            ranges_to_send,
            sequencer,
            writer,
            digesters,
            download_strategy,
            read_handle,
        )
    )

    try:
      writer.stop()
    except BrokenPipeError:
      if download_strategy == cloud_api.DownloadStrategy.ONE_SHOT:
        log.info(
            'Writing to download stream raised broken pipe error during '
            'writer.stop().'
        )
        destination_pipe_is_broken = True
      else:
        raise
    success = True

  finally:
    bidi_read_object_rpc.close()
    if not success and writer.is_alive:
      try:
        writer.stop()
      except Exception as e:  # pylint: disable=broad-except
        log.debug('Ignored exception while stopping DecoupledWriter: %s', e)

  return _MrdRpcResult(
      processed_bytes=writer.processed_bytes,
      destination_pipe_is_broken=destination_pipe_is_broken,
      received_read_handle=received_read_handle,
  )


def _handle_mrd_bidi_responses(
    gapic_client: Any,
    bidi_read_object_rpc: Any,
    ranges_to_send: list[Any],
    sequencer: OffsetSequencer,
    writer: AsyncDecoupledWriter,
    digesters: dict[hash_util.HashAlgorithm, hash_util.HashObject],
    download_strategy: cloud_api.DownloadStrategy,
    received_read_handle: Any,
) -> tuple[Any, bool]:
  """Processes responses from the bidi_read_object_rpc and feeds data to the writer."""
  destination_pipe_is_broken = False

  while bidi_read_object_rpc.is_active:
    try:
      bidi_read_object_response = bidi_read_object_rpc.recv()
      if (
          bidi_read_object_response
          and bidi_read_object_response.read_handle
          and bidi_read_object_response.read_handle.handle
      ):
        received_read_handle = bidi_read_object_response.read_handle

      for object_range_data in bidi_read_object_response.object_data_ranges:
        data = object_range_data.checksummed_data.content
        if data:
          expected_crc = None
          if _should_validate_chunk_integrity(digesters):
            expected_crc = object_range_data.checksummed_data.crc32c

          sequencer.add_chunk(
              object_range_data.read_range.read_offset, data, expected_crc
          )

          for (
              seq_offset,
              seq_data,
              seq_expected_crc,
          ) in sequencer.yield_sequential_chunks():
            try:
              writer.write(seq_offset, seq_data, seq_expected_crc)
            except BrokenPipeError:
              if download_strategy == cloud_api.DownloadStrategy.ONE_SHOT:
                log.info('Writing to download stream raised broken pipe error.')
                destination_pipe_is_broken = True
                break
              raise

        if object_range_data.range_end and ranges_to_send:
          next_range = ranges_to_send.pop(0)
          next_request = gapic_client.types.BidiReadObjectRequest(
              read_ranges=[next_range]
          )
          bidi_read_object_rpc.send(next_request)
          if not ranges_to_send:
            bidi_read_object_rpc.requests_done()

      if destination_pipe_is_broken:
        break

    except (StopIteration, EOFError):
      break
    except Exception as e:  # pylint: disable=broad-except
      if grpc_retry_util.is_retriable(exc_value=e):
        log.debug('Retriable network error during rpc: %s', e)
        break
      raise

  return received_read_handle, destination_pipe_is_broken
