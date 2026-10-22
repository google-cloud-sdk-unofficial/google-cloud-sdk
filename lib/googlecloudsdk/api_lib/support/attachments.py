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
"""Uploads files as attachments to Cloud Support cases."""

import urllib.parse

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.credentials import requests as creds_requests

_SUPPORT_UPLOAD_CHUNK_BYTES = 8 * 1024 * 1024
# Start a resumable upload session on the case. The attachment filename
# must be passed as a query parameter (the API rejects it in the request
# body with "File name is missing"). Bytes are then streamed to the
# session URL returned in the X-Goog-Upload-URL response header, so the
# archive never lands on the local disk and peak memory stays at one chunk.
_SUPPORT_UPLOAD_START_PATH = (
    '/upload/v2/{parent}/attachments'
    '?attachment.filename={filename}&upload_protocol=resumable')


class UploadError(core_exceptions.Error):
  """The Cloud Support API rejected a step of an attachment upload."""


def BuildUploadStartUrl(case_name, filename):
  """Builds the resumable upload start URL for a support case attachment."""
  endpoint = apis.GetEffectiveApiEndpoint('cloudsupport', 'v2').rstrip('/')
  return (endpoint + _SUPPORT_UPLOAD_START_PATH).format(
      parent=case_name, filename=urllib.parse.quote(filename, safe=''))


def _RaiseAttachFailed(response, case_name, filename):
  """Raises an error indicating an attachment upload has failed."""
  raise UploadError(
      'Failed to attach [{}] to support case [{}] (HTTP {}): {}'.format(
          filename, case_name, response.status_code, response.text[:500]))


def UploadFromStream(case_name, filename, source, size_bytes,
                     chunk_bytes=_SUPPORT_UPLOAD_CHUNK_BYTES):
  """Uploads a stream of bytes as a new attachment on a Cloud Support case.

  Starts a resumable upload session on the case, sends the bytes from source
  in chunk_bytes-sized requests, and finalizes the upload with the remaining
  (possibly empty) bytes. Nothing is written to local disk, and memory use is
  proportional to chunk_bytes rather than to the attachment size. The
  attachment is uploaded with content type application/zip.

  Args:
    case_name: str, the case resource name: projects/PROJECT/cases/CASE or
      organizations/ORG/cases/CASE.
    filename: str, the attachment filename shown on the case.
    source: An iterable of bytes objects, consumed once and in order. Pieces
      can have any size; they are re-buffered into chunk_bytes-sized
      requests. For example, response.iter_content(chunk_size=...) of a
      streaming requests response, or a generator. Not read at all if the
      upload session cannot be started.
    size_bytes: int, the total number of bytes that source yields. Only used
      to report progress.
    chunk_bytes: int, the number of bytes sent in each request before the
      final one.

  Returns:
    dict, the created Attachment resource parsed from the API response.

  Raises:
    UploadError: If the API rejects the start of the upload, a chunk, or the
      final request. The message includes the HTTP status and the first 500
      characters of the response body.
  """
  session = creds_requests.GetSession()
  start = session.post(BuildUploadStartUrl(case_name, filename), headers={
      'Content-Length': '0',
      'X-Goog-Upload-Protocol': 'resumable',
      'X-Goog-Upload-Command': 'start',
      'X-Goog-Upload-Header-Content-Type': 'application/zip',
  })
  upload_url = start.headers.get('X-Goog-Upload-URL')
  if start.status_code != 200 or not upload_url:
    raise UploadError(
        'Failed to start the upload to support case [{}] (HTTP {}): {}'.format(
            case_name, start.status_code, start.text[:500]))

  offset = 0
  with progress_tracker.ProgressTracker(
      'Attaching [{}] ({:.1f} MiB) to support case [{}]'.format(
          filename, size_bytes / (1024 * 1024), case_name)):
    buffered = bytearray()
    for piece in source:
      buffered.extend(piece)
      while len(buffered) >= chunk_bytes:
        block = bytes(buffered[:chunk_bytes])
        del buffered[:chunk_bytes]
        response = session.put(upload_url, data=block, headers={
            'X-Goog-Upload-Command': 'upload',
            'X-Goog-Upload-Offset': str(offset),
        })
        if response.status_code != 200:
          _RaiseAttachFailed(response, case_name, filename)
        offset += len(block)
    # The final block (possibly empty) finalizes the upload and returns the
    # created attachment.
    response = session.put(upload_url, data=bytes(buffered), headers={
        'X-Goog-Upload-Command': 'upload, finalize',
        'X-Goog-Upload-Offset': str(offset),
    })
    if response.status_code != 200:
      _RaiseAttachFailed(response, case_name, filename)
  return response.json()
