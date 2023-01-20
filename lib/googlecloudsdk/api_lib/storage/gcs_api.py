# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Client for interacting with Google Cloud Storage.

Implements CloudApi for the GCS JSON API. Example functions include listing
buckets, uploading objects, and setting lifecycle conditions.

TODO(b/160601969): Update class with remaining API methods for ls and cp.
    Note, this class has not been tested against the GCS API yet.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import json

from apitools.base.py import encoding_helper
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from apitools.base.py import transfer as apitools_transfer

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as cloud_errors
from googlecloudsdk.api_lib.storage import gcs_download
from googlecloudsdk.api_lib.storage import gcs_error_util
from googlecloudsdk.api_lib.storage import gcs_metadata_util
from googlecloudsdk.api_lib.storage import gcs_upload
from googlecloudsdk.api_lib.storage import patch_gcs_messages
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import gzip_util
from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util
from googlecloudsdk.command_lib.storage.tasks.cp import download_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests
from googlecloudsdk.core.credentials import transports
from googlecloudsdk.core.util import scaled_integer

import six


# TODO(b/171296237): Remove this when fixes are submitted in apitools.
patch_gcs_messages.patch()


# Call the progress callback every PROGRESS_CALLBACK_THRESHOLD bytes to
# improve performance.
KB = 1024  # Bytes.
MINIMUM_PROGRESS_CALLBACK_THRESHOLD = 512 * KB
# The API limits the number of objects that can be composed in a single call.
# https://cloud.google.com/storage/docs/json_api/v1/objects/compose
MAX_OBJECTS_PER_COMPOSE_CALL = 32

# Determines which IAM format to use as new features are added.
_IAM_POLICY_VERSION = 3
_NOTIFICATION_PAYLOAD_FORMAT_KEY_TO_API_CONSTANT = {
    cloud_api.NotificationPayloadFormat.JSON: 'JSON_API_V1',
    cloud_api.NotificationPayloadFormat.NONE: 'NONE',
}


def get_download_serialization_data(object_resource, progress):
  """Generates download serialization data for Apitools.

  Args:
    object_resource (resource_reference.ObjectResource): Used to get metadata.
    progress (int): Represents how much of download is complete.

  Returns:
    JSON string for use with Apitools.
  """
  serialization_dict = {
      'auto_transfer': False,  # Apitools JSON API feature not used.
      'progress': progress,
      'total_size': object_resource.size,
      'url': object_resource.metadata.mediaLink,  # HTTP download link.
  }
  return json.dumps(serialization_dict)


class _StorageStreamResponseHandler(requests.ResponseHandler):
  """Handler for writing the streaming response to the download stream."""

  def __init__(self):
    """Initializes response handler for requests downloads."""
    super(_StorageStreamResponseHandler, self).__init__(use_stream=True)
    self._stream = None
    self._digesters = {}
    self._processed_bytes = 0,
    self._progress_callback = None
    self._size = None

    self._chunk_size = scaled_integer.ParseInteger(
        properties.VALUES.storage.download_chunk_size.Get())
    # If progress callbacks is called more frequently than every 512 KB, it
    # can degrate performance.
    self._progress_callback_threshold = max(MINIMUM_PROGRESS_CALLBACK_THRESHOLD,
                                            self._chunk_size)

  def update_destination_info(self, stream,
                              size,
                              digesters=None,
                              processed_bytes=0,
                              progress_callback=None):
    """Updates the stream handler with destination information.

    The download_http_client object is stored on the gcs_api object. This allows
    resusing the same http_client when the gcs_api is cached using
    threading.local, which improves performance.
    Since this same object gets used for mutliple downloads, we need to update
    the stream handler with the current active download's destination.

    Args:
      stream (stream): Local stream to write downloaded data to.
      size (int): The amount of data in bytes to be downloaded.
      digesters (dict<HashAlgorithm, hashlib object> | None): For updating hash
        digests of downloaded objects on the fly.
      processed_bytes (int): For keeping track of how much progress has been
        made.
      progress_callback (func<int>): Accepts processed_bytes and submits
        progress info for aggregation.
    """
    self._stream = stream
    self._size = size
    self._digesters = digesters if digesters is not None else {}
    self._processed_bytes = processed_bytes
    self._progress_callback = progress_callback
    self._start_byte = self._processed_bytes

  def handle(self, source_stream):
    if self._stream is None:
      raise ValueError('Stream was not found.')

    # Start reading the raw stream.
    bytes_since_last_progress_callback = 0
    while True:
      data = source_stream.read(self._chunk_size)
      if data:
        self._stream.write(data)

        for hash_object in self._digesters.values():
          hash_object.update(data)

        self._processed_bytes += len(data)
        bytes_since_last_progress_callback += len(data)
        if (self._progress_callback and bytes_since_last_progress_callback >=
            self._progress_callback_threshold):
          self._progress_callback(self._processed_bytes)
          bytes_since_last_progress_callback = (
              bytes_since_last_progress_callback -
              self._progress_callback_threshold)
      else:
        if self._progress_callback and bytes_since_last_progress_callback:
          # Make a last progress callback call to update the final size.
          self._progress_callback(self._processed_bytes)
        break

    total_downloaded_data = self._processed_bytes - self._start_byte
    if self._size != total_downloaded_data:
      # The input stream terminated before the entire content was read,
      # possibly due to a network condition.
      message = (
          'Download not completed. Target size={}, downloaded data={}'.format(
              self._size, total_downloaded_data))
      log.debug(message)
      raise cloud_errors.RetryableApiError(message)


def _get_encryption_headers(key):
  if (key and key != user_request_args_factory.CLEAR and
      key.type == encryption_util.KeyType.CSEK):
    return {
        'x-goog-encryption-algorithm': 'AES256',
        'x-goog-encryption-key': key.key,
        'x-goog-encryption-key-sha256': key.sha256,
    }
  return {}


class GcsApi(cloud_api.CloudApi):
  """Client for Google Cloud Storage API."""

  capabilities = {
      cloud_api.Capability.COMPOSE_OBJECTS,
      cloud_api.Capability.RESUMABLE_UPLOAD,
      cloud_api.Capability.SLICED_DOWNLOAD,
      cloud_api.Capability.ENCRYPTION,
      cloud_api.Capability.DAISY_CHAIN_SEEKABLE_UPLOAD_STREAM,
  }

  def __init__(self):
    super(GcsApi, self).__init__()
    self.client = core_apis.GetClientInstance('storage', 'v1')
    self.client.overwrite_transfer_urls_with_client_base = True
    self.messages = core_apis.GetMessagesModule('storage', 'v1')
    self._stream_response_handler = _StorageStreamResponseHandler()
    self._download_http_client = None
    self._upload_http_client = None

  @contextlib.contextmanager
  def _apitools_request_headers_context(self, headers):
    if headers:
      old_headers = self.client.additional_http_headers.copy()
      self.client.additional_http_headers.update(headers)
    yield
    if headers:
      self.client.additional_http_headers = old_headers

  def _encryption_headers_context(self, key):
    return self._apitools_request_headers_context(_get_encryption_headers(key))

  def _encryption_headers_for_rewrite_call_context(self, request_config):
    additional_headers = {}
    encryption_key = getattr(request_config.resource_args, 'encryption_key',
                             None)
    additional_headers.update(_get_encryption_headers(encryption_key))

    decryption_key = getattr(request_config.resource_args, 'decryption_key',
                             None)
    if decryption_key and decryption_key.type == encryption_util.KeyType.CSEK:
      additional_headers.update({
          'x-goog-copy-source-encryption-algorithm': 'AES256',
          'x-goog-copy-source-encryption-key': decryption_key.key,
          'x-goog-copy-source-encryption-key-sha256': decryption_key.sha256,
      })
    return self._apitools_request_headers_context(additional_headers)

  def _get_projection(self, fields_scope, message_class):
    """Generate query projection from fields_scope.

    Args:
      fields_scope (FieldsScope): Used to determine projection to return.
      message_class (object): Apitools message object that contains a projection
        enum.

    Returns:
      projection (ProjectionValueValuesEnum): Determines if ACL properties
          should be returned.

    Raises:
      ValueError: The fields_scope isn't recognized.
    """
    try:
      if fields_scope not in cloud_api.FieldsScope:
        raise ValueError('Invalid fields_scope.')
    except TypeError:
      raise ValueError('Invalid fields_scope.')
    projection_enum = message_class.ProjectionValueValuesEnum

    if fields_scope == cloud_api.FieldsScope.FULL:
      return projection_enum.full
    return projection_enum.noAcl

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def create_bucket(self,
                    bucket_resource,
                    request_config,
                    fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    projection = self._get_projection(fields_scope,
                                      self.messages.StorageBucketsInsertRequest)

    bucket_metadata = self.messages.Bucket(
        name=bucket_resource.storage_url.bucket_name)
    gcs_metadata_util.update_bucket_metadata_from_request_config(
        bucket_metadata, request_config)

    request = self.messages.StorageBucketsInsertRequest(
        bucket=bucket_metadata,
        project=properties.VALUES.core.project.GetOrFail(),
        projection=projection)

    created_bucket_metadata = self.client.buckets.Insert(request)
    return gcs_metadata_util.get_bucket_resource_from_metadata(
        created_bucket_metadata)

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def delete_bucket(self, bucket_name, request_config):
    """See super class."""
    request = self.messages.StorageBucketsDeleteRequest(
        bucket=bucket_name,
        ifMetagenerationMatch=request_config.precondition_metageneration_match)
    # Success returns an empty body.
    # https://cloud.google.com/storage/docs/json_api/v1/buckets/delete
    self.client.buckets.Delete(request)

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def get_bucket(self, bucket_name, fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    projection = self._get_projection(fields_scope,
                                      self.messages.StorageBucketsGetRequest)
    request = self.messages.StorageBucketsGetRequest(
        bucket=bucket_name,
        projection=projection)

    metadata = self.client.buckets.Get(request)
    return gcs_metadata_util.get_bucket_resource_from_metadata(metadata)

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def get_bucket_iam_policy(self, bucket_name):
    """See super class."""
    global_params = self.messages.StandardQueryParameters(
        fields='bindings,etag')
    return self.client.buckets.GetIamPolicy(
        self.messages.StorageBucketsGetIamPolicyRequest(
            bucket=bucket_name,
            optionsRequestedPolicyVersion=_IAM_POLICY_VERSION),
        global_params=global_params)

  def list_buckets(self, fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    projection = self._get_projection(fields_scope,
                                      self.messages.StorageBucketsListRequest)
    request = self.messages.StorageBucketsListRequest(
        project=properties.VALUES.core.project.GetOrFail(),
        projection=projection)

    global_params = None
    if fields_scope == cloud_api.FieldsScope.SHORT:
      global_params = self.messages.StandardQueryParameters(
          fields='items/name,nextPageToken')
    # TODO(b/160238394) Decrypt metadata fields if necessary.
    bucket_iter = list_pager.YieldFromList(
        self.client.buckets,
        request,
        batch_size=cloud_api.NUM_ITEMS_PER_LIST_PAGE,
        global_params=global_params)
    try:
      for bucket in bucket_iter:
        yield gcs_metadata_util.get_bucket_resource_from_metadata(bucket)
    except apitools_exceptions.HttpError as e:
      core_exceptions.reraise(
          cloud_errors.translate_error(e, gcs_error_util.ERROR_TRANSLATION))

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def patch_bucket(self,
                   bucket_resource,
                   request_config,
                   fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    projection = self._get_projection(fields_scope,
                                      self.messages.StorageBucketsPatchRequest)
    metadata = bucket_resource.metadata or (
        gcs_metadata_util.get_apitools_metadata_from_url(
            bucket_resource.storage_url))
    gcs_metadata_util.update_bucket_metadata_from_request_config(
        metadata, request_config)

    cleared_fields = gcs_metadata_util.get_cleared_bucket_fields(request_config)
    if (metadata.defaultObjectAcl and metadata.defaultObjectAcl[0]
        == gcs_metadata_util.PRIVATE_DEFAULT_OBJECT_ACL):
      cleared_fields.append('defaultObjectAcl')
      metadata.defaultObjectAcl = []

    # Must null out existing ACLs to apply new ones.
    if request_config.predefined_acl_string:
      cleared_fields.append('acl')
      predefined_acl = getattr(
          self.messages.StorageBucketsPatchRequest.PredefinedAclValueValuesEnum,
          request_config.predefined_acl_string)
    else:
      predefined_acl = None

    if request_config.predefined_default_object_acl_string:
      cleared_fields.append('defaultObjectAcl')
      predefined_default_object_acl = getattr(
          self.messages.StorageBucketsPatchRequest
          .PredefinedDefaultObjectAclValueValuesEnum,
          request_config.predefined_default_object_acl_string)
    else:
      predefined_default_object_acl = None

    apitools_request = self.messages.StorageBucketsPatchRequest(
        bucket=bucket_resource.storage_url.bucket_name,
        bucketResource=metadata,
        projection=projection,
        ifMetagenerationMatch=request_config.precondition_metageneration_match,
        predefinedAcl=predefined_acl,
        predefinedDefaultObjectAcl=predefined_default_object_acl)

    with self.client.IncludeFields(cleared_fields):
      return gcs_metadata_util.get_bucket_resource_from_metadata(
          self.client.buckets.Patch(apitools_request))

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def set_bucket_iam_policy(self, bucket_name, policy):
    """See super class."""
    return self.client.buckets.SetIamPolicy(
        self.messages.StorageBucketsSetIamPolicyRequest(
            bucket=bucket_name, policy=policy))

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def compose_objects(self,
                      source_resources,
                      destination_resource,
                      request_config,
                      original_source_resource=None):
    """See CloudApi class for function doc strings."""

    if not source_resources:
      raise cloud_errors.GcsApiError(
          'Compose requires at least one component object.')

    if len(source_resources) > MAX_OBJECTS_PER_COMPOSE_CALL:
      raise cloud_errors.GcsApiError(
          'Compose was called with {} objects. The limit is {}.'.format(
              len(source_resources), MAX_OBJECTS_PER_COMPOSE_CALL))

    source_messages = []
    for source in source_resources:
      source_message = self.messages.ComposeRequest.SourceObjectsValueListEntry(
          name=source.storage_url.object_name)
      if source.storage_url.generation is not None:
        generation = int(source.storage_url.generation)
        source_message.generation = generation
      source_messages.append(source_message)

    base_destination_metadata = gcs_metadata_util.get_apitools_metadata_from_url(
        destination_resource.storage_url)
    if getattr(source_resources[0], 'metadata', None):
      final_destination_metadata = gcs_metadata_util.copy_object_metadata(
          source_resources[0].metadata, base_destination_metadata,
          request_config)
    else:
      final_destination_metadata = base_destination_metadata
    if original_source_resource and isinstance(
        original_source_resource, resource_reference.FileObjectResource):
      original_source_file_path = (
          original_source_resource.storage_url.object_name)
    else:
      original_source_file_path = None
    gcs_metadata_util.update_object_metadata_from_request_config(
        final_destination_metadata, request_config, original_source_file_path)

    compose_request_payload = self.messages.ComposeRequest(
        sourceObjects=source_messages, destination=final_destination_metadata)

    compose_request = self.messages.StorageObjectsComposeRequest(
        composeRequest=compose_request_payload,
        destinationBucket=destination_resource.storage_url.bucket_name,
        destinationObject=destination_resource.storage_url.object_name,
        ifGenerationMatch=request_config.precondition_generation_match,
        ifMetagenerationMatch=request_config.precondition_metageneration_match)

    if request_config.resource_args:
      encryption_key = request_config.resource_args.encryption_key
      if (encryption_key and
          encryption_key != user_request_args_factory.CLEAR and
          encryption_key.type == encryption_util.KeyType.CMEK):
        compose_request.kmsKeyName = encryption_key.key

    if request_config.predefined_acl_string is not None:
      compose_request.destinationPredefinedAcl = getattr(
          self.messages.StorageObjectsComposeRequest
          .DestinationPredefinedAclValueValuesEnum,
          request_config.predefined_acl_string)

    encryption_key = getattr(request_config.resource_args, 'encryption_key',
                             None)
    with self._encryption_headers_context(encryption_key):
      return gcs_metadata_util.get_object_resource_from_metadata(
          self.client.objects.Compose(compose_request))

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def copy_object(self,
                  source_resource,
                  destination_resource,
                  request_config,
                  should_deep_copy_metadata=False,
                  progress_callback=None):
    """See super class."""
    destination_metadata = getattr(destination_resource, 'metadata', None)
    if not destination_metadata:
      destination_metadata = gcs_metadata_util.get_apitools_metadata_from_url(
          destination_resource.storage_url)
    if source_resource.metadata:
      destination_metadata = gcs_metadata_util.copy_object_metadata(
          source_resource.metadata,
          destination_metadata,
          request_config,
          should_deep_copy=should_deep_copy_metadata)
    gcs_metadata_util.update_object_metadata_from_request_config(
        destination_metadata, request_config)

    if request_config.predefined_acl_string:
      predefined_acl = getattr(
          self.messages.StorageObjectsRewriteRequest
          .DestinationPredefinedAclValueValuesEnum,
          request_config.predefined_acl_string)
    else:
      predefined_acl = None

    if source_resource.generation is None:
      source_generation = None
    else:
      source_generation = int(source_resource.generation)

    tracker_file_path = tracker_file_util.get_tracker_file_path(
        destination_resource.storage_url,
        tracker_file_util.TrackerFileType.REWRITE,
        source_url=source_resource.storage_url)
    rewrite_parameters_hash = tracker_file_util.hash_gcs_rewrite_parameters_for_tracker_file(
        source_resource,
        destination_resource,
        destination_metadata,
        request_config=request_config)

    resume_rewrite_token = (
        tracker_file_util.get_rewrite_token_from_tracker_file(
            tracker_file_path, rewrite_parameters_hash))
    if resume_rewrite_token:
      log.debug('Found rewrite token. Resuming copy.')
    else:
      log.debug('No rewrite token found. Starting copy from scratch.')

    max_bytes_per_call = scaled_integer.ParseInteger(
        properties.VALUES.storage.copy_chunk_size.Get())
    with self._encryption_headers_for_rewrite_call_context(request_config):
      while True:
        request = self.messages.StorageObjectsRewriteRequest(
            sourceBucket=source_resource.storage_url.bucket_name,
            sourceObject=source_resource.storage_url.object_name,
            destinationBucket=destination_resource.storage_url.bucket_name,
            destinationObject=destination_resource.storage_url.object_name,
            object=destination_metadata,
            sourceGeneration=source_generation,
            ifGenerationMatch=copy_util.get_generation_match_value(
                request_config),
            ifMetagenerationMatch=request_config
            .precondition_metageneration_match,
            destinationPredefinedAcl=predefined_acl,
            rewriteToken=resume_rewrite_token,
            maxBytesRewrittenPerCall=max_bytes_per_call)

        encryption_key = getattr(
            request_config.resource_args, 'encryption_key', None)
        if (encryption_key and
            encryption_key != user_request_args_factory.CLEAR and
            encryption_key.type == encryption_util.KeyType.CMEK):
          # This key is also provided in destination_metadata.kmsKeyName by
          # update_object_metadata_from_request_config. This has no effect on
          # the copy object request, which references the field below, and is a
          # side-effect of logic required for uploads and compose operations.
          request.destinationKmsKeyName = encryption_key.key

        rewrite_response = self.client.objects.Rewrite(request)
        processed_bytes = rewrite_response.totalBytesRewritten
        if progress_callback:
          progress_callback(processed_bytes)

        if rewrite_response.done:
          break

        if not resume_rewrite_token:
          resume_rewrite_token = rewrite_response.rewriteToken
          if source_resource.size >= scaled_integer.ParseInteger(
              properties.VALUES.storage.resumable_threshold.Get()):
            tracker_file_util.write_rewrite_tracker_file(
                tracker_file_path, rewrite_parameters_hash,
                rewrite_response.rewriteToken)

    tracker_file_util.delete_tracker_file(tracker_file_path)
    return gcs_metadata_util.get_object_resource_from_metadata(
        rewrite_response.resource)

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def delete_object(self, object_url, request_config):
    """See super class."""
    # S3 requires a string, but GCS uses an int for generation.
    if object_url.generation is not None:
      generation = int(object_url.generation)
    else:
      generation = None

    request = self.messages.StorageObjectsDeleteRequest(
        bucket=object_url.bucket_name,
        object=object_url.object_name,
        generation=generation,
        ifGenerationMatch=request_config.precondition_generation_match,
        ifMetagenerationMatch=request_config.precondition_metageneration_match)
    # Success returns an empty body.
    # https://cloud.google.com/storage/docs/json_api/v1/objects/delete
    self.client.objects.Delete(request)

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def download_object(self,
                      cloud_resource,
                      download_stream,
                      request_config,
                      digesters=None,
                      do_not_decompress=False,
                      download_strategy=cloud_api.DownloadStrategy.RESUMABLE,
                      progress_callback=None,
                      start_byte=0,
                      end_byte=None):
    """See super class."""
    if (request_config.system_posix_data and cloud_resource.metadata and
        cloud_resource.metadata.metadata):
      custom_metadata_dict = encoding_helper.MessageToDict(
          cloud_resource.metadata.metadata)
      posix_attributes_to_set = (
          posix_util.get_posix_attributes_from_custom_metadata_dict(
              cloud_resource.storage_url.url_string, custom_metadata_dict))
    else:
      posix_attributes_to_set = None

    if (not posix_util.are_file_permissions_valid(
        cloud_resource.storage_url.url_string, request_config.system_posix_data,
        posix_attributes_to_set) or
        download_util.return_and_report_if_nothing_to_download(
            cloud_resource, progress_callback)):
      return cloud_api.DownloadApiClientReturnValue(
          posix_attributes=posix_attributes_to_set,
          server_reported_encoding=None)

    serialization_data = get_download_serialization_data(
        cloud_resource, start_byte)
    apitools_download = apitools_transfer.Download.FromData(
        download_stream,
        serialization_data,
        num_retries=properties.VALUES.storage.max_retries.GetInt(),
        client=self.client)

    self._stream_response_handler.update_destination_info(
        stream=download_stream,
        size=(end_byte - start_byte + 1
              if end_byte is not None else cloud_resource.size),
        digesters=digesters,
        processed_bytes=start_byte,
        progress_callback=progress_callback)

    if self._download_http_client is None:
      self._download_http_client = transports.GetApitoolsTransport(
          response_encoding=None,
          response_handler=self._stream_response_handler)
    apitools_download.bytes_http = self._download_http_client

    additional_headers = {}
    if do_not_decompress:
      # TODO(b/161453101): Optimize handling of gzip-encoded downloads.
      additional_headers['accept-encoding'] = 'gzip'

    decryption_key = getattr(request_config.resource_args, 'decryption_key',
                             None)
    additional_headers.update(_get_encryption_headers(decryption_key))

    if download_strategy == cloud_api.DownloadStrategy.ONE_SHOT:
      server_reported_encoding = gcs_download.launch(
          apitools_download,
          start_byte=start_byte,
          end_byte=end_byte,
          additional_headers=additional_headers)
    else:
      server_reported_encoding = gcs_download.launch_retriable(
          download_stream,
          apitools_download,
          start_byte=start_byte,
          end_byte=end_byte,
          additional_headers=additional_headers)

    return cloud_api.DownloadApiClientReturnValue(
        posix_attributes=posix_attributes_to_set,
        server_reported_encoding=server_reported_encoding)

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def get_object_iam_policy(self, bucket_name, object_name, generation=None):
    """See super class."""
    if generation:
      generation = int(generation)

    global_params = self.messages.StandardQueryParameters(
        fields='bindings,etag')
    return self.client.objects.GetIamPolicy(
        self.messages.StorageObjectsGetIamPolicyRequest(
            bucket=bucket_name, object=object_name, generation=generation),
        global_params=global_params)

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def get_object_metadata(self,
                          bucket_name,
                          object_name,
                          request_config=None,
                          generation=None,
                          fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""

    # S3 requires a string, but GCS uses an int for generation.
    if generation:
      generation = int(generation)

    projection = self._get_projection(fields_scope,
                                      self.messages.StorageObjectsGetRequest)

    decryption_key = getattr(
        getattr(request_config, 'resource_args', None), 'decryption_key', None)
    with self._encryption_headers_context(decryption_key):
      object_metadata = self.client.objects.Get(
          self.messages.StorageObjectsGetRequest(
              bucket=bucket_name,
              object=object_name,
              generation=generation,
              projection=projection))
    return gcs_metadata_util.get_object_resource_from_metadata(object_metadata)

  def list_objects(self,
                   bucket_name,
                   prefix=None,
                   delimiter=None,
                   all_versions=None,
                   fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    projection = self._get_projection(fields_scope,
                                      self.messages.StorageObjectsListRequest)
    global_params = None
    if fields_scope == cloud_api.FieldsScope.SHORT:
      global_params = self.messages.StandardQueryParameters(
          fields='prefixes,items/name,items/size,items/generation,nextPageToken'
      )

    object_list = None
    while True:
      apitools_request = self.messages.StorageObjectsListRequest(
          bucket=bucket_name,
          prefix=prefix,
          delimiter=delimiter,
          versions=all_versions,
          projection=projection,
          pageToken=object_list.nextPageToken if object_list else None,
          maxResults=cloud_api.NUM_ITEMS_PER_LIST_PAGE)

      try:
        object_list = self.client.objects.List(
            apitools_request, global_params=global_params)
      except apitools_exceptions.HttpError as e:
        core_exceptions.reraise(
            cloud_errors.translate_error(e, gcs_error_util.ERROR_TRANSLATION))

      # Yield objects.
      # TODO(b/160238394) Decrypt metadata fields if necessary.
      for object_metadata in object_list.items:
        object_metadata.bucket = bucket_name
        yield gcs_metadata_util.get_object_resource_from_metadata(
            object_metadata)

      # Yield prefixes.
      for prefix_string in object_list.prefixes:
        yield resource_reference.PrefixResource(
            storage_url.CloudUrl(
                scheme=storage_url.ProviderPrefix.GCS,
                bucket_name=bucket_name,
                object_name=prefix_string),
            prefix=prefix_string)

      if not object_list.nextPageToken:
        break

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def patch_object_metadata(self,
                            bucket_name,
                            object_name,
                            object_resource,
                            request_config,
                            fields_scope=cloud_api.FieldsScope.NO_ACL,
                            generation=None):
    """See super class."""
    # S3 requires a string, but GCS uses an int for generation.
    if generation:
      generation = int(generation)

    predefined_acl = None
    if request_config.predefined_acl_string:
      predefined_acl = getattr(
          self.messages.StorageObjectsPatchRequest.PredefinedAclValueValuesEnum,
          request_config.predefined_acl_string)

    projection = self._get_projection(fields_scope,
                                      self.messages.StorageObjectsPatchRequest)

    object_metadata = object_resource.metadata or (
        gcs_metadata_util.get_apitools_metadata_from_url(
            object_resource.storage_url))

    gcs_metadata_util.update_object_metadata_from_request_config(
        object_metadata, request_config)

    request = self.messages.StorageObjectsPatchRequest(
        bucket=bucket_name,
        object=object_name,
        objectResource=object_metadata,
        generation=generation,
        ifGenerationMatch=request_config.precondition_generation_match,
        ifMetagenerationMatch=request_config.precondition_metageneration_match,
        predefinedAcl=predefined_acl,
        projection=projection)

    updated_metadata = self.client.objects.Patch(request)
    return gcs_metadata_util.get_object_resource_from_metadata(updated_metadata)

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def set_object_iam_policy(self,
                            bucket_name,
                            object_name,
                            policy,
                            generation=None):
    """See super class."""
    if generation:
      generation = int(generation)
    return self.client.objects.SetIamPolicy(
        self.messages.StorageObjectsSetIamPolicyRequest(
            bucket=bucket_name,
            object=object_name,
            generation=generation,
            policy=policy))

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def upload_object(self,
                    source_stream,
                    destination_resource,
                    request_config,
                    source_resource=None,
                    serialization_data=None,
                    tracker_callback=None,
                    upload_strategy=cloud_api.UploadStrategy.SIMPLE):
    """See CloudApi class for function doc strings."""
    if self._upload_http_client is None:
      self._upload_http_client = transports.GetApitoolsTransport(
          redact_request_body_reason=(
              'Object data is not displayed to keep the log output clean.'
              ' Set log_http_show_request_body property to True to print the'
              ' body of this request.'))

    if source_resource:
      source_path = source_resource.storage_url.versionless_url_string
    else:
      source_path = None
    should_gzip_in_flight = gzip_util.should_gzip_in_flight(
        request_config.gzip_settings, source_path)
    if should_gzip_in_flight:
      log.info(
          'Using compressed transport encoding for {}.'.format(source_path))
    if upload_strategy == cloud_api.UploadStrategy.SIMPLE:
      upload = gcs_upload.SimpleUpload(self, self._upload_http_client,
                                       source_stream, destination_resource,
                                       should_gzip_in_flight, request_config,
                                       source_resource)
    elif upload_strategy == cloud_api.UploadStrategy.RESUMABLE:
      upload = gcs_upload.ResumableUpload(self, self._upload_http_client,
                                          source_stream, destination_resource,
                                          should_gzip_in_flight, request_config,
                                          source_resource, serialization_data,
                                          tracker_callback)
    elif upload_strategy == cloud_api.UploadStrategy.STREAMING:
      upload = gcs_upload.StreamingUpload(self, self._upload_http_client,
                                          source_stream, destination_resource,
                                          should_gzip_in_flight, request_config,
                                          source_resource)
    else:
      raise command_errors.Error('Invalid upload strategy: {}.'.format(
          upload_strategy.value))

    encryption_key = getattr(request_config.resource_args, 'encryption_key',
                             None)
    try:
      with self._encryption_headers_context(encryption_key):
        metadata = upload.run()
    except (
        apitools_exceptions.StreamExhausted,
        apitools_exceptions.TransferError,
    ) as error:
      raise cloud_errors.ResumableUploadAbortError(
          '{}\n This likely occurred because the file being uploaded changed '
          'size between resumable upload attempts. If this error persists, try '
          'deleting the tracker files present in {}'.format(
              str(error),
              properties.VALUES.storage.tracker_files_directory.Get()))

    return gcs_metadata_util.get_object_resource_from_metadata(metadata)

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def get_service_agent(self, project_id=None, project_number=None):
    """See CloudApi class for doc strings."""
    if project_id:
      project_identifier = project_id
    elif project_number:
      project_identifier = six.text_type(project_number)
    else:
      project_identifier = properties.VALUES.core.project.GetOrFail()
    return self.client.projects_serviceAccount.Get(
        self.messages.StorageProjectsServiceAccountGetRequest(
            projectId=project_identifier)).email_address

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def create_notification_configuration(
      self,
      url,
      pubsub_topic,
      custom_attributes=None,
      event_types=None,
      object_name_prefix=None,
      payload_format=cloud_api.NotificationPayloadFormat.JSON):
    """See CloudApi class for doc strings."""
    if not url.is_bucket():
      raise ValueError(
          'Create notification configuration endpoint accepts only bucket URLs.'
      )
    notification_configuration = self.messages.Notification(
        topic=pubsub_topic,
        payload_format=_NOTIFICATION_PAYLOAD_FORMAT_KEY_TO_API_CONSTANT[
            payload_format])
    if custom_attributes:
      additional_properties = []
      for key, value in custom_attributes.items():
        additional_properties.append((
            self.messages.Notification.CustomAttributesValue.AdditionalProperty(
                key=key, value=value)))
      notification_configuration.custom_attributes = (
          self.messages.Notification.CustomAttributesValue(
              additionalProperties=additional_properties))
    if event_types:
      notification_configuration.event_types = [
          event_type.value for event_type in event_types
      ]
    if object_name_prefix:
      notification_configuration.object_name_prefix = object_name_prefix

    return self.client.notifications.Insert(
        self.messages.StorageNotificationsInsertRequest(
            bucket=url.bucket_name,
            notification=notification_configuration,
            userProject=properties.VALUES.core.project.GetOrFail()))

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def delete_notification_configuration(self, url, notification_id):
    """See CloudApi class for doc strings."""
    if not url.is_bucket():
      raise ValueError(
          'Delete notification configuration endpoint accepts only bucket URLs.'
      )
    self.client.notifications.Delete(
        self.messages.StorageNotificationsDeleteRequest(
            bucket=url.bucket_name,
            notification=notification_id,
            userProject=properties.VALUES.core.project.GetOrFail()))

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def get_notification_configuration(self, url, notification_id):
    """See CloudApi class for doc strings."""
    if not url.is_bucket():
      raise ValueError(
          'Get notification configuration endpoint accepts only bucket URLs.')
    return self.client.notifications.Get(
        self.messages.StorageNotificationsGetRequest(
            bucket=url.bucket_name,
            notification=notification_id,
            userProject=properties.VALUES.core.project.GetOrFail()))

  @gcs_error_util.catch_http_error_raise_gcs_api_error()
  def list_notification_configurations(self, url):
    """See CloudApi class for function doc strings."""
    if not url.is_bucket():
      raise ValueError(
          'List notification configurations endpoint accepts only bucket URLs.')

    response = self.client.notifications.List(
        self.messages.StorageNotificationsListRequest(
            bucket=url.bucket_name,
            userProject=properties.VALUES.core.project.GetOrFail()))
    for notification_configuration in response.items:
      yield notification_configuration
